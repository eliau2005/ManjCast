"""
Cast streaming module for ManjCast.
Integrates device discovery and screen capture functionality to stream to Cast devices.
"""

import logging
import time
import tempfile
import os
from typing import Optional, List, Dict
from datetime import datetime
import pychromecast
from pychromecast.controllers.media import MediaController

from .device_discovery import CastDeviceScanner, DeviceDiscoveryError
from .screen_capture import ScreenCaptureManager, DisplayServer
from .stream_server import StreamServer

# Configure logging
logger = logging.getLogger(__name__)

class CastStreamer:
    """
    Manages the streaming of screen capture to Cast devices.
    Integrates device discovery and screen capture functionality.
    """
    
    def __init__(self, web_root: str = None):
        """Initialize the Cast streamer."""
        self._device_scanner = CastDeviceScanner()
        self._screen_capture = ScreenCaptureManager()
        self._stream_server = StreamServer(web_root=web_root)
        self._current_device = None
        self._current_stream = None
        self._streaming = False
        self._temp_dir = None
        self._settings = {
            'capture_type': 'fullscreen',  # or 'window'
            'window_id': None,             # Window ID when capture_type is 'window'
            'receiver_id': 'C0868879',     # Default Cast receiver app ID
        }
        
    def discover_devices(self) -> List[Dict]:
        """
        Scan for available Cast devices.
        
        Returns:
            List[Dict]: List of discovered devices
        """
        try:
            devices = self._device_scanner.start_discovery()
            if not devices:
                logger.info("No Cast devices found")
            return devices
        except DeviceDiscoveryError as e:
            logger.error(f"Failed to discover devices: {e}")
            raise
    
    def select_device(self, device_info: Dict) -> bool:
        """
        Select a Cast device for streaming.
        
        Args:
            device_info: Dictionary containing device information
            
        Returns:
            bool: True if device was selected successfully
        """
        try:
            # Connect to the selected device
            chromecasts, browser = pychromecast.get_chromecasts()
            for cc in chromecasts:
                if str(cc.device.uuid) == device_info['uuid']:
                    cc.wait()  # Wait for device to be ready
                    self._current_device = cc
                    logger.info(f"Selected device: {cc.device.friendly_name}")
                    return True
            
            logger.error(f"Device {device_info['name']} not found")
            return False
            
        except Exception as e:
            logger.error(f"Failed to select device: {e}")
            raise
    
    def start_streaming(self) -> bool:
        """
        Start streaming screen capture to the selected Cast device.
        
        Returns:
            bool: True if streaming started successfully
        """
        if not self._current_device:
            raise RuntimeError("No Cast device selected")
        
        try:
            # Create temporary directory for stream files if needed
            if not self._temp_dir:
                self._temp_dir = tempfile.mkdtemp(prefix="manjcast_")
            
            # Configure capture settings
            capture_settings = {
                'capture_type': self._settings['capture_type'],
                'window_id': self._settings.get('window_id')
            }
            self._screen_capture.settings = capture_settings
            
            # Start screen capture
            output_file = os.path.join(self._temp_dir, "stream.mp4")
            self._current_stream = self._screen_capture.start_capture(output_file)
            
            # Start streaming server
            ip, port = self._stream_server.start(output_file)

            # Prepare media info with metadata
            media_info = {
                'contentId': f"http://{ip}:{port}/stream.mp4",
                'contentType': 'video/mp4',
                'streamType': 'LIVE',
                'metadata': {
                    'type': 0,  # GENERIC_TYPE
                    'metadataType': 0,  # GENERIC
                    'title': 'ManjCast Screen Share',
                    'subtitle': f'Sharing from {os.uname().nodename}',
                    'images': []
                }
            }

            # Initialize media controller with improved settings
            mc = self._current_device.media_controller
            mc.play_media(
                media_info['contentId'],
                content_type=media_info['contentType'],
                stream_type=media_info['streamType'],
                metadata=media_info['metadata'],
                autoplay=True,
                current_time=0,
                title=media_info['metadata']['title']
            )
            mc.block_until_active()

            # Set default volume if not set
            if self._current_device.status.volume_level is None:
                self._current_device.set_volume(0.5)
            
            self._streaming = True
            logger.info(f"Started streaming to {self._current_device.device.friendly_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start streaming: {e}")
            self._cleanup_stream()
            raise
    
    def stop_streaming(self):
        """Stop the current streaming session."""
        try:
            if self._streaming:
                # Stop screen capture
                if self._current_stream:
                    self._screen_capture.stop_capture(self._current_stream)
                    self._current_stream = None
                
                # Stop streaming server
                if self._stream_server:
                    self._stream_server.stop()
                
                # Stop media playback
                if self._current_device:
                    mc = self._current_device.media_controller
                    mc.stop()
                
                self._streaming = False
                logger.info("Streaming stopped")
                
        except Exception as e:
            logger.error(f"Error while stopping stream: {e}")
            raise
        finally:
            self._cleanup_stream()
    
    def _cleanup_stream(self):
        """Clean up temporary streaming resources."""
        try:
            if self._temp_dir and os.path.exists(self._temp_dir):
                import shutil
                shutil.rmtree(self._temp_dir)
                self._temp_dir = None
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary files: {e}")
    
    @property
    def is_streaming(self) -> bool:
        """Check if currently streaming."""
        return self._streaming
    
    @property
    def current_device(self) -> Optional[str]:
        """Get the name of the currently selected device."""
        if self._current_device:
            return self._current_device.device.friendly_name
        return None
    
    @property
    def settings(self) -> dict:
        """Get current streamer settings."""
        return self._settings.copy()
    
    @settings.setter
    def settings(self, new_settings: dict):
        """Update streamer settings."""
        self._settings.update(new_settings)
    
    def __del__(self):
        """Clean up resources when the object is destroyed."""
        self.stop_streaming()