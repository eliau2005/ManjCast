#!/usr/bin/env python3
# ManjCast - Screen Casting Tool for Manjaro Linux
# Device Discovery Module

import logging
import threading
import time
from typing import List, Dict, Callable, Optional, Any, Set, Tuple, Union

# Handle imports with better error handling for IDE resolution
try:
    import pychromecast
    from pychromecast.discovery import CastBrowser, SimpleCastListener
    from pychromecast.controllers.media import MediaController
    PYCHROMECAST_AVAILABLE = True
except ImportError:
    # Create placeholder types for type checking when module isn't available
    PYCHROMECAST_AVAILABLE = False
    class DummyChromecast:
        """Dummy class when pychromecast is not available"""
        pass
    # Create dummy classes for type hinting
    class CastBrowser:
        def __init__(self, *args, **kwargs):
            pass
        def start_discovery(self):
            pass
        def stop_discovery(self):
            pass
    class SimpleCastListener:
        def __init__(self, *args, **kwargs):
            pass

try:
    from zeroconf import ServiceBrowser, Zeroconf
    ZEROCONF_AVAILABLE = True
except ImportError:
    ZEROCONF_AVAILABLE = False
    # Create dummy classes for IDE type resolution
    class ServiceBrowser:
        """Dummy class when zeroconf is not available"""
        def __init__(self, *args, **kwargs):
            pass
        def cancel(self):
            pass
            
    class Zeroconf:
        """Dummy class when zeroconf is not available"""
        def close(self):
            pass

logger = logging.getLogger("ManjCast.DeviceDiscovery")

class DeviceDiscovery:
    """Handles discovery of Google Cast compatible devices on the network"""
    
    def __init__(self, cast_manager):
        self.cast_manager = cast_manager
        self.devices: Dict[str, Dict[str, Any]] = {}  # Dictionary to store discovered devices
        self.browser: Optional[CastBrowser] = None
        self.listener: Optional[SimpleCastListener] = None
        self.zeroconf: Optional[Zeroconf] = None
        self._discovery_thread: Optional[threading.Thread] = None
        self._stop_discovery = threading.Event()
        self.discovery_callbacks: List[Callable[[Dict[str, Dict[str, Any]]], None]] = []  # Callbacks to be called when devices are discovered
        self._known_devices: Dict[str, pychromecast.Chromecast] = {}
        
    def start_discovery(self):
        """Start the device discovery process"""
        if self._discovery_thread and self._discovery_thread.is_alive():
            logger.info("Discovery is already running")
            return
            
        self._stop_discovery.clear()
        self._discovery_thread = threading.Thread(target=self._discover_devices)
        self._discovery_thread.daemon = True
        self._discovery_thread.start()
        logger.info("Device discovery started")
        
    def stop_discovery(self):
        """Stop the device discovery process"""
        if self._discovery_thread and self._discovery_thread.is_alive():
            self._stop_discovery.set()
            self._discovery_thread.join(timeout=5)
            logger.info("Device discovery stopped")
        
        # Clean up browser resources
        if self.browser:
            self.browser.stop_discovery()
            self.browser = None
        
        # Clean up zeroconf resources
        if self.zeroconf:
            self.zeroconf.close()
            self.zeroconf = None
            
    def register_callback(self, callback: Callable[[Dict[str, Dict[str, Any]]], None]):
        """Register a callback to be called when devices change"""
        if callback not in self.discovery_callbacks:
            self.discovery_callbacks.append(callback)
            
    def unregister_callback(self, callback: Callable):
        """Remove a previously registered callback"""
        if callback in self.discovery_callbacks:
            self.discovery_callbacks.remove(callback)
            
    def get_devices(self) -> Dict[str, Dict[str, Any]]:
        """Get the list of currently discovered devices"""
        return self.devices
    
    def _discover_devices(self):
        """Background thread that discovers Cast devices"""
        if not PYCHROMECAST_AVAILABLE or not ZEROCONF_AVAILABLE:
            logger.error("Cannot discover devices: pychromecast or zeroconf package is missing")
            return
            
        try:
            # Initialize zeroconf for discovery
            self.zeroconf = Zeroconf()
            
            # Create a listener for the browser
            self.listener = SimpleCastListener()
            self.listener.add_callback(self._cast_discovered_callback)
            
            # Create and start the cast browser
            self.browser = CastBrowser(self.listener, zeroconf=self.zeroconf)
            self.browser.start_discovery()
            
            # Run the discovery loop
            while not self._stop_discovery.is_set():
                # Wait for a period before refreshing
                self._stop_discovery.wait(timeout=5)
                
                # Check for new devices periodically
                if not self._stop_discovery.is_set():
                    self._update_devices()
        
        except Exception as e:
            logger.error(f"Fatal error in device discovery: {e}")
        finally:
            # Clean up resources
            self.stop_discovery()
    
    def _cast_discovered_callback(self, cast):
        """Callback for when a cast device is discovered"""
        try:
            uuid = str(cast.uuid)
            self._known_devices[uuid] = cast
            self._update_devices()
        except Exception as e:
            logger.error(f"Error in cast discovery callback: {e}")
            
    def _update_devices(self):
        """Update the list of devices and notify callbacks"""
        try:
            # Build the new device list from known devices
            new_devices: Dict[str, Dict[str, Any]] = {}
            
            for uuid, cast in self._known_devices.items():
                try:
                    # Get device info
                    device_info = {
                        'name': cast.device.friendly_name,
                        'model_name': cast.device.model_name,
                        'uuid': str(cast.uuid),
                        'cast_type': cast.device.cast_type,
                        'address': cast.device.host,
                        'port': cast.device.port,
                        'cast_object': cast,
                        'status': 'available'
                    }
                    new_devices[uuid] = device_info
                except Exception as e:
                    logger.error(f"Error getting device info for {uuid}: {e}")
            
            # Check if the device list has changed
            if new_devices != self.devices:
                self.devices = new_devices
                logger.info(f"Discovered {len(self.devices)} cast devices")
                
                # Notify callbacks about the updated device list
                for callback in self.discovery_callbacks:
                    try:
                        callback(self.devices)
                    except Exception as e:
                        logger.error(f"Error in device discovery callback: {e}")
                        
        except Exception as e:
            logger.error(f"Error updating devices: {e}")
    
    def connect_to_device(self, device_uuid: str) -> Optional[Any]:
        """Connect to a specific device"""
        if not PYCHROMECAST_AVAILABLE:
            logger.error("Cannot connect to device: pychromecast package is missing")
            return None
            
        if device_uuid in self.devices:
            device = self.devices[device_uuid]
            try:
                cast = device['cast_object']
                cast.wait()  # Wait for the device to be ready
                return cast
            except Exception as e:
                logger.error(f"Error connecting to device {device['name']}: {e}")
        else:
            logger.error(f"Device with UUID {device_uuid} not found")
        return None
