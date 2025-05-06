"""
Device discovery module for finding Google Cast devices on the network.
Uses PyChromecast for reliable device discovery.
"""

import socket
import logging
from typing import List, Dict
import pychromecast
from pychromecast.discovery import discover_chromecasts
from pychromecast.dial import get_device_info

logger = logging.getLogger(__name__)

class DeviceDiscoveryError(Exception):
    """Exception raised for errors during device discovery."""
    pass

class CastDeviceScanner:
    """Handles discovery of Google Cast devices on the network."""
    
    def __init__(self, timeout: int = 5):
        """Initialize device discovery.
        
        Args:
            timeout: Discovery timeout in seconds
        """
        self.timeout = timeout
    
    def start_discovery(self) -> List[Dict]:
        """Find Google Cast devices on the local network.
        
        Returns:
            List of discovered devices with their properties
        """
        try:
            logger.info("Starting device discovery...")
            devices = []
            
            # Use PyChromecast's discovery mechanism
            chromecasts, browser = pychromecast.discover_chromecasts(timeout=self.timeout)
            
            for cc in chromecasts:
                try:
                    # Get detailed device info
                    device_info = get_device_info(cc.host)
                    if device_info:
                        device = {
                            'name': cc.device.friendly_name,
                            'model': device_info.model_name,
                            'ip_address': cc.host,
                            'port': cc.port,
                            'uuid': str(cc.uuid),
                            'manufacturer': device_info.manufacturer
                        }
                        devices.append(device)
                        logger.info(f"Found device: {device['name']} at {device['ip_address']}")
                except Exception as e:
                    logger.warning(f"Error getting device info for {cc.host}: {e}")
                    continue
            
            # Stop discovery browser
            browser.stop_discovery()
            
            if not devices:
                logger.warning("No Cast devices found on the network")
            else:
                logger.info(f"Found {len(devices)} Cast devices")
            
            return devices
            
        except Exception as e:
            logger.error(f"Error during device discovery: {e}")
            raise DeviceDiscoveryError(f"Device discovery failed: {str(e)}")
    
    @staticmethod
    def verify_device(ip_address: str, port: int = 8009) -> bool:
        """Verify if a device is reachable and supports Cast protocol.
        
        Args:
            ip_address: Device IP address
            port: Device port (default: 8009)
            
        Returns:
            True if device is valid and reachable
        """
        try:
            # Try to connect to verify device is reachable
            sock = socket.create_connection((ip_address, port), timeout=2)
            sock.close()
            
            # Get device info to verify it's a Cast device
            device_info = get_device_info(ip_address)
            return device_info is not None
            
        except Exception as e:
            logger.warning(f"Device verification failed for {ip_address}: {e}")
            return False