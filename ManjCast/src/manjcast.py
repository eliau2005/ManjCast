#!/usr/bin/env python3
# ManjCast - Screen Casting Tool for Manjaro Linux
# Main application entry point

import sys
import os
import logging
import configparser
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

# Import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui.main_window import MainWindow
from ui.system_tray import SystemTrayIcon
from src.device_discovery import DeviceDiscovery
from src.cast_manager import CastManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser("~/.local/share/manjcast/logs/manjcast.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ManjCast")

class ManjCast:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("ManjCast")
        self.app.setQuitOnLastWindowClosed(False)
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize components
        self.cast_manager = CastManager(self.config)
        self.device_discovery = DeviceDiscovery(self.cast_manager)
        
        # Setup UI
        self.main_window = MainWindow(self.cast_manager, self.device_discovery)
        self.tray_icon = SystemTrayIcon(self.main_window, self.cast_manager)
        self.tray_icon.show()
        
        logger.info("ManjCast initialized successfully")
    
    def _load_config(self):
        """Load configuration from the config file"""
        config = configparser.ConfigParser()
        
        # Default config path
        config_dir = os.path.expanduser("~/.config/manjcast")
        config_path = os.path.join(config_dir, "config.ini")
        
        # Create config directory if it doesn't exist
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        # If config doesn't exist, copy from installation directory
        if not os.path.exists(config_path):
            default_config = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                "config.ini"
            )
            if os.path.exists(default_config):
                import shutil
                shutil.copy2(default_config, config_path)
        
        # Read config file
        if os.path.exists(config_path):
            config.read(config_path)
        else:
            # Create default config
            config["GENERAL"] = {
                "first_run": "true",
                "minimize_to_tray": "true",
                "start_with_system": "false"
            }
            config["CASTING"] = {
                "resolution": "1080p",
                "framerate": "30",
                "audio_enabled": "true",
                "preferred_device": ""
            }
            config["ADVANCED"] = {
                "discovery_timeout": "5",
                "buffer_size": "8192",
                "log_level": "INFO"
            }
            
            # Save default config
            with open(config_path, 'w') as config_file:
                config.write(config_file)
        
        return config
    
    def run(self):
        """Run the application"""
        # Show main window if this is the first run
        if self.config.get('GENERAL', 'first_run', fallback='true') == 'true':
            self.main_window.show()
            # Update first_run setting
            self.config['GENERAL']['first_run'] = 'false'
            config_path = os.path.expanduser("~/.config/manjcast/config.ini")
            with open(config_path, 'w') as config_file:
                self.config.write(config_file)
        
        # Start device discovery
        self.device_discovery.start_discovery()
        
        # Run event loop
        return self.app.exec_()


def main():
    # Create necessary directories
    os.makedirs(os.path.expanduser("~/.local/share/manjcast/logs"), exist_ok=True)
    
    # Start application
    manjcast = ManjCast()
    sys.exit(manjcast.run())


if __name__ == "__main__":
    main()
