"""
Screen capture module for ManjCast.
Handles screen capture functionality with support for both Xorg and Wayland.
"""

import logging
import subprocess
import shutil
import os
from typing import Optional, Dict
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

class DisplayServer(Enum):
    """Enum representing the display server type."""
    XORG = "xorg"
    WAYLAND = "wayland"
    UNKNOWN = "unknown"

class ScreenCaptureManager:
    """Manages screen capture functionality with support for different display servers."""
    
    def __init__(self):
        """Initialize the screen capture manager."""
        self._display_server = self._detect_display_server()
        self._ffmpeg_path = shutil.which('ffmpeg')
        if not self._ffmpeg_path:
            raise RuntimeError("ffmpeg is not installed. Please install it first.")
        
        # Default capture settings
        self._settings = {
            'framerate': 30,
            'video_codec': 'libx264',      # Using h264 for Chromecast compatibility
            'pixel_format': 'yuv420p',     # Required for Chromecast
            'preset': 'ultrafast',         # Minimize latency
            'tune': 'zerolatency',        # Optimize for streaming
            'segment_time': 2,            # Split output into 2-second segments
            'format': 'mp4'               # Output format
        }

    def _detect_display_server(self) -> DisplayServer:
        """
        Detect the current display server (Xorg or Wayland).
        
        Returns:
            DisplayServer: The detected display server type
        """
        session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
        if session_type == 'wayland' or os.environ.get('WAYLAND_DISPLAY'):
            return DisplayServer.WAYLAND
        elif session_type == 'x11' or os.environ.get('DISPLAY'):
            return DisplayServer.XORG
        return DisplayServer.UNKNOWN

    def _get_input_options(self) -> Dict[str, str]:
        """
        Get the appropriate FFmpeg input options based on the display server.
        
        Returns:
            Dict[str, str]: FFmpeg input options
        """
        if self._display_server == DisplayServer.WAYLAND:
            return {
                'f': 'pipewire',
                'framerate': str(self._settings['framerate'])
            }
        else:
            return {
                'f': 'x11grab',
                'framerate': str(self._settings['framerate']),
                's': self._get_screen_resolution(),
                'draw_mouse': '1',
                'i': os.environ.get('DISPLAY', ':0.0')
            }

    def _get_screen_resolution(self) -> str:
        """
        Get the current screen resolution.
        
        Returns:
            str: Screen resolution in the format "WIDTHxHEIGHT"
        """
        try:
            if self._display_server == DisplayServer.WAYLAND:
                # Try using environment variables first
                width = os.environ.get('WINDOWWIDTH', '1920')
                height = os.environ.get('WINDOWHEIGHT', '1080')
                return f"{width}x{height}"
            else:
                # Use xrandr for X11
                output = subprocess.check_output(['xrandr', '--current'], text=True)
                for line in output.split('\n'):
                    if '*' in line:  # Current resolution is marked with *
                        resolution = line.split()[0]
                        return resolution
        except (subprocess.SubprocessError, FileNotFoundError, IndexError):
            logger.warning("Could not detect screen resolution, using default 1920x1080")
        
        return "1920x1080"

    def start_capture(self, output_file: str) -> subprocess.Popen:
        """
        Start screen capture and save to the specified output file.
        
        Args:
            output_file: Path where to save the captured video
            
        Returns:
            subprocess.Popen: The FFmpeg process object
        """
        try:
            input_options = self._get_input_options()
            
            # Start ffmpeg process with appropriate input options
            command = [
                self._ffmpeg_path,
                '-hide_banner',
                '-loglevel', 'error'
            ]
            
            # Add input options
            for key, value in input_options.items():
                command.extend([f'-{key}', str(value)])
            
            # Add output options for Chromecast compatibility
            command.extend([
                '-c:v', self._settings['video_codec'],
                '-pix_fmt', self._settings['pixel_format'],
                '-preset', self._settings['preset'],
                '-tune', self._settings['tune'],
                '-g', str(self._settings['framerate'] * 2),  # GOP size = 2 seconds
                '-r', str(self._settings['framerate']),
                '-f', 'segment',                             # Enable segmented output
                '-segment_time', str(self._settings['segment_time']),
                '-segment_format', self._settings['format'],
                '-segment_wrap', '2',                        # Keep only 2 segments
                output_file
            ])
            
            # Log the command for debugging
            logger.debug(f"FFmpeg command: {' '.join(command)}")
            
            # Start the FFmpeg process
            logger.info(f"Starting screen capture with {self._display_server.value}")
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Check if process started successfully
            if process.poll() is not None:
                error = process.stderr.read().decode() if process.stderr else "Unknown error"
                raise RuntimeError(f"Failed to start FFmpeg: {error}")
            
            return process
            
        except Exception as e:
            logger.error(f"Failed to start screen capture: {e}")
            raise

    def stop_capture(self, process: subprocess.Popen):
        """
        Stop the screen capture process.
        
        Args:
            process: The FFmpeg process to stop
        """
        if process and process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            logger.info("Screen capture stopped")

    @property
    def settings(self) -> dict:
        """Get current capture settings."""
        return self._settings.copy()
    
    @settings.setter
    def settings(self, new_settings: dict):
        """
        Update capture settings.
        
        Args:
            new_settings: Dictionary with new settings
        """
        self._settings.update(new_settings)
        
    @property
    def display_server(self) -> DisplayServer:
        """Get the current display server type."""
        return self._display_server