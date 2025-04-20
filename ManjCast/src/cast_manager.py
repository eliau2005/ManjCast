#!/usr/bin/env python3
# ManjCast - Screen Casting Tool for Manjaro Linux
# Cast Manager Module

import logging
import threading
import time
import socket
import os
import json
import tempfile
import subprocess
from typing import Dict, Optional, Tuple
import pychromecast
from pychromecast.controllers.media import MediaController

from src.screen_capture import ScreenCapture
from src.audio_capture import AudioCapture

logger = logging.getLogger("ManjCast.CastManager")

class CastManager:
    """Manages the casting session and handles communication with Cast devices"""
    
    def __init__(self, config):
        self.config = config
        self.current_device = None
        self.cast_session = None
        self.is_casting = False
        self.capture_thread = None
        self.stop_casting_event = threading.Event()
        
        # Initialize components
        self.screen_capture = ScreenCapture(config)
        self.audio_capture = AudioCapture(config)
        
        # HTTP server for media streaming
        self.http_server = None
        self.http_server_port = self._find_available_port()
        self.streaming_url = None
        
        # Cast settings
        self.cast_mode = "screen"  # "screen" or "window"
        self.window_id = None
        self.audio_enabled = config.getboolean('CASTING', 'audio_enabled', fallback=True)
        
        # Status callback
        self.status_callbacks = []
    
    def _find_available_port(self) -> int:
        """Find an available port for the HTTP server"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        return port
    
    def select_device(self, device_uuid: str) -> bool:
        """Select a device for casting"""
        # Avoid circular import by importing only in this method
        device_discovery = None
        
        # Try to find the device in existing discovered devices
        if device_uuid and hasattr(self, '_device_discovery') and self._device_discovery:
            device_discovery = self._device_discovery
            if device_uuid in device_discovery.devices:
                device = device_discovery.devices[device_uuid]
                try:
                    cast = device['cast_object']
                    cast.wait()
                    self.current_device = cast
                    logger.info(f"Selected device: {cast.device.friendly_name}")
                    return True
                except Exception as e:
                    logger.error(f"Error connecting to device: {e}")
                    return False
        
        # If device not found or no discovery instance, create one
        if not device_discovery:
            from src.device_discovery import DeviceDiscovery
            device_discovery = DeviceDiscovery(self)
            self._device_discovery = device_discovery
            
        # Start discovery if needed
        if not device_discovery.devices:
            device_discovery.start_discovery()
            time.sleep(2)  # Give it a moment to discover devices
        
        # Connect to the selected device
        cast = device_discovery.connect_to_device(device_uuid)
        if cast:
            self.current_device = cast
            logger.info(f"Selected device: {cast.device.friendly_name}")
            return True
        else:
            logger.error(f"Failed to select device with UUID {device_uuid}")
            return False
    
    def set_cast_mode(self, mode: str, window_id: Optional[str] = None):
        """Set the casting mode (screen or window)"""
        if mode not in ["screen", "window"]:
            raise ValueError("Cast mode must be 'screen' or 'window'")
        
        self.cast_mode = mode
        if mode == "window" and window_id is not None:
            self.window_id = window_id
        
        logger.info(f"Cast mode set to {mode}" + 
                    (f" with window ID {window_id}" if mode == "window" else ""))
    
    def set_audio_enabled(self, enabled: bool):
        """Enable or disable audio casting"""
        self.audio_enabled = enabled
        logger.info(f"Audio casting {'enabled' if enabled else 'disabled'}")
    
    def start_casting(self) -> bool:
        """Start the casting session"""
        if self.is_casting:
            logger.warning("Already casting, please stop the current session first")
            return False
        
        if not self.current_device:
            logger.error("No device selected for casting")
            return False
        
        try:
            # Reset the stop event
            self.stop_casting_event.clear()
            
            # Start capture based on the selected mode
            if self.cast_mode == "screen":
                success = self.screen_capture.start_capture()
            else:  # window mode
                if not self.window_id:
                    logger.error("No window selected for window casting mode")
                    return False
                success = self.screen_capture.start_capture(window_id=self.window_id)
            
            if not success:
                logger.error("Failed to start screen capture")
                return False
            
            # Start audio capture if enabled
            if self.audio_enabled:
                success = self.audio_capture.start_capture()
                if not success:
                    logger.warning("Failed to start audio capture, continuing without audio")
            
            # Start the HTTP server for streaming
            self._start_streaming_server()
            
            # Start the casting thread
            self.capture_thread = threading.Thread(target=self._casting_thread)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            
            self.is_casting = True
            self._notify_status_change("started")
            logger.info("Casting started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting casting: {e}")
            self.stop_casting()
            return False
    
    def stop_casting(self):
        """Stop the current casting session"""
        if not self.is_casting:
            return
        
        # Signal the casting thread to stop
        self.stop_casting_event.set()
        
        # Wait for the thread to finish
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=5)
        
        # Stop screen capture
        self.screen_capture.stop_capture()
        
        # Stop audio capture if it was enabled
        if self.audio_enabled:
            self.audio_capture.stop_capture()
        
        # Stop HTTP server
        self._stop_streaming_server()
        
        # Reset state
        self.is_casting = False
        self._notify_status_change("stopped")
        logger.info("Casting stopped")
    
    def register_status_callback(self, callback):
        """Register a callback to be notified of status changes"""
        if callback not in self.status_callbacks:
            self.status_callbacks.append(callback)
    
    def unregister_status_callback(self, callback):
        """Unregister a previously registered status callback"""
        if callback in self.status_callbacks:
            self.status_callbacks.remove(callback)
    
    def _notify_status_change(self, status):
        """Notify all registered callbacks of a status change"""
        for callback in self.status_callbacks:
            try:
                callback(status)
            except Exception as e:
                logger.error(f"Error in status callback: {e}")
    
    def _start_streaming_server(self):
        """Start the HTTP server for streaming content to the Cast device"""
        # Create a temporary directory for the streaming files
        temp_dir = tempfile.mkdtemp(prefix="manjcast_")
        
        # Create an HLS playlist
        playlist_path = os.path.join(temp_dir, "stream.m3u8")
        segment_template = os.path.join(temp_dir, "segment_%03d.ts")
        
        # Build the streaming URL
        local_ip = self._get_local_ip()
        self.streaming_url = f"http://{local_ip}:{self.http_server_port}/stream.m3u8"
        
        # Detect if we're using Wayland
        wayland_session = os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
        
        # Start the HTTP server process
        # Using ffmpeg to create an HTTP server with HLS streaming
        ffmpeg_cmd = ["ffmpeg"]
        
        # Select input format based on desktop environment and session type
        if wayland_session:
            # For Wayland sessions, use wlstream or pipewire
            try:
                # Check if wf-recorder is available for Wayland
                subprocess.check_output(["which", "wf-recorder"], stderr=subprocess.PIPE)
                # Use a pipe from wf-recorder
                wf_recorder_cmd = [
                    "wf-recorder", "--muxer=v4l2", "--codec=rawvideo", "--file=/dev/stdout", 
                    "-g", f"{self.screen_capture.screen_dimensions[0]}x{self.screen_capture.screen_dimensions[1]}"
                ]
                ffmpeg_input_process = subprocess.Popen(
                    wf_recorder_cmd, 
                    stdout=subprocess.PIPE
                )
                # Set input options for ffmpeg
                ffmpeg_cmd.extend([
                    "-f", "v4l2",
                    "-framerate", self.config.get('CASTING', 'framerate', fallback='30'),
                    "-video_size", self._get_resolution(),
                    "-i", "pipe:"
                ])
            except:
                # Fallback to x11grab even on Wayland (works with XWayland)
                logger.warning("wf-recorder not found, falling back to x11grab under Wayland")
                ffmpeg_cmd.extend([
                    "-f", "x11grab",
                    "-r", self.config.get('CASTING', 'framerate', fallback='30'),
                    "-s", self._get_resolution(),
                    "-i", self.screen_capture.get_display() + (f"+{self.window_id}" if self.cast_mode == "window" else ""),
                ])
        else:
            # Standard X11 capture
            ffmpeg_cmd.extend([
                "-f", "x11grab",
                "-r", self.config.get('CASTING', 'framerate', fallback='30'),
                "-s", self._get_resolution(),
                "-i", self.screen_capture.get_display() + (f"+{self.window_id}" if self.cast_mode == "window" else ""),
            ])
        
        # Add audio input if enabled
        if self.audio_enabled:
            ffmpeg_cmd.extend([
                "-f", "pulse",
                "-ac", "2",
                "-i", self.audio_capture.get_source(),
            ])
        
        # Add output options
        ffmpeg_cmd.extend([
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-c:a", "aac" if self.audio_enabled else "none",
            "-f", "hls",
            "-hls_time", "2",
            "-hls_list_size", "5",
            "-hls_flags", "delete_segments",
            "-hls_segment_filename", segment_template,
            "-method", "PUT",
            playlist_path
        ])
        
        # Start the ffmpeg process
        logger.info(f"Starting ffmpeg with command: {' '.join(ffmpeg_cmd)}")
        self.http_server = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Start a simple HTTP server to serve the HLS playlist
        http_server_cmd = [
            "python", "-m", "http.server", str(self.http_server_port),
            "--directory", temp_dir
        ]
        
        self.http_server = subprocess.Popen(
            http_server_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give the server a moment to start
        time.sleep(1)
        logger.info(f"Streaming server started on {self.streaming_url}")
    
    def _stop_streaming_server(self):
        """Stop the HTTP streaming server"""
        if self.http_server:
            self.http_server.terminate()
            try:
                self.http_server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.http_server.kill()
            self.http_server = None
            logger.info("Streaming server stopped")
        
        self.streaming_url = None
    
    def _casting_thread(self):
        """Background thread that handles the casting session"""
        try:
            if not self.current_device:
                logger.error("No device selected for casting")
                return
            
            # Connect to the device
            cast = self.current_device
            cast.wait()
            
            # Create a media controller
            mc = cast.media_controller
            
            # Start the media playback
            mc.play_media(
                self.streaming_url,
                content_type="application/x-mpegURL",
                stream_type="LIVE",
                title=f"ManjCast - {socket.gethostname()}"
            )
            mc.block_until_active()
            
            # Monitor and keep the session alive
            while not self.stop_casting_event.is_set():
                # Check the status periodically
                status = mc.status
                if status and status.player_state in ["PLAYING", "BUFFERING"]:
                    pass  # All good
                elif status:
                    logger.warning(f"Unexpected player state: {status.player_state}")
                    # Try to resume playback if it stopped
                    if status.player_state == "IDLE":
                        mc.play_media(
                            self.streaming_url,
                            content_type="application/x-mpegURL",
                            stream_type="LIVE",
                            title=f"ManjCast - {socket.gethostname()}"
                        )
                
                # Check if the cast device is still connected
                if not cast.is_connected:
                    logger.warning("Lost connection to the cast device")
                    self._notify_status_change("disconnected")
                    break
                
                # Sleep for a while before checking again
                time.sleep(1)
            
            # Stop casting when done
            mc.stop()
            
        except Exception as e:
            logger.error(f"Error in casting thread: {e}")
            self._notify_status_change("error")
        finally:
            # Make sure casting is properly stopped
            self.stop_casting()
    
    def _get_local_ip(self) -> str:
        """Get the local IP address of this computer"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Doesn't need to be reachable
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip
    
    def _get_resolution(self) -> str:
        """Get the screen resolution for capturing"""
        resolution = self.config.get('CASTING', 'resolution', fallback='1080p')
        
        # Convert common resolution names to actual dimensions
        if resolution == "1080p":
            return "1920x1080"
        elif resolution == "720p":
            return "1280x720"
        elif resolution == "480p":
            return "854x480"
        else:
            # Assume it's already in the format WIDTHxHEIGHT
            return resolution
