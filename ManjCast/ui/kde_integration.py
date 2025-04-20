#!/usr/bin/env python3
# ManjCast - Screen Casting Tool for Manjaro Linux
# KDE Desktop Environment Integration

import os
import logging
import subprocess
from typing import Optional, Dict, Callable

try:
    from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
    from PyQt5.QtGui import QIcon
    from PyQt5.QtCore import QProcess
    from PyQt5.QtDBus import QDBusConnection, QDBusInterface
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

logger = logging.getLogger("ManjCast.UI.KdeIntegration")

class KdeIntegration:
    """Provides integration with KDE Plasma desktop environment"""
    
    def __init__(self):
        self.is_kde = self._check_if_kde()
        self.dbus_connection = None
        
        # Initialize DBus connection if running in KDE
        if self.is_kde and PYQT_AVAILABLE:
            self.dbus_connection = QDBusConnection.sessionBus()
    
    def _check_if_kde(self) -> bool:
        """Check if running in a KDE Plasma session"""
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        if "kde" in desktop:
            return True
        
        # Alternative check
        try:
            output = subprocess.check_output(["ps", "-e"]).decode()
            if "plasmashell" in output or "kwin" in output:
                return True
        except Exception as e:
            logger.error(f"Error checking for KDE: {e}")
        
        return False
    
    def setup_indicator(self, callback: Callable) -> bool:
        """KDE already has good support for QSystemTrayIcon - no special implementation needed"""
        if not self.is_kde or not PYQT_AVAILABLE:
            logger.warning("Cannot set up KDE integration - not running in KDE or PyQt not available")
            return False
            
        logger.info("KDE already supports Qt system tray - no special setup needed")
        return True
    
    def setup_autostart(self, enable: bool = True) -> bool:
        """Set up or remove autostart entry for KDE"""
        if not self.is_kde:
            logger.warning("Cannot set up KDE autostart - not running in KDE")
            return False
        
        try:
            autostart_dir = os.path.expanduser("~/.config/autostart")
            autostart_file = os.path.join(autostart_dir, "manjcast.desktop")
            
            if enable:
                # Create autostart directory if it doesn't exist
                os.makedirs(autostart_dir, exist_ok=True)
                
                # Create desktop entry
                with open(autostart_file, 'w') as f:
                    f.write("""[Desktop Entry]
Type=Application
Name=ManjCast
Comment=Screen casting for Manjaro
Exec=manjcast
Icon=video-display
Terminal=false
Categories=Qt;KDE;Utility;
X-KDE-StartupNotify=true
X-KDE-autostart-after=panel
X-KDE-autostart-phase=2
X-DBUS-ServiceName=org.manjcast
""")
                logger.info("KDE autostart enabled")
                return True
                
            else:
                # Remove autostart entry if it exists
                if os.path.exists(autostart_file):
                    os.remove(autostart_file)
                    logger.info("KDE autostart disabled")
                return True
                
        except Exception as e:
            logger.error(f"Error setting up KDE autostart: {e}")
            return False
    
    def get_current_workspace(self) -> int:
        """Get the current KDE workspace number"""
        if not self.is_kde:
            return 0
        
        try:
            # Try using DBus first (more reliable)
            if PYQT_AVAILABLE and self.dbus_connection.isConnected():
                kwin_interface = QDBusInterface(
                    "org.kde.KWin", 
                    "/KWin", 
                    "org.kde.KWin", 
                    self.dbus_connection
                )
                
                if kwin_interface.isValid():
                    current_desktop = kwin_interface.call("currentDesktop").arguments()[0]
                    return current_desktop - 1  # KWin desktops are 1-indexed
            
            # Fallback to wmctrl
            output = subprocess.check_output(["wmctrl", "-d"]).decode()
            for line in output.split('\n'):
                if '*' in line:  # Current workspace is marked with *
                    parts = line.split()
                    if parts:
                        return int(parts[0])
                        
        except Exception as e:
            logger.error(f"Error getting current KDE workspace: {e}")
        
        return 0
    
    def get_screen_info(self) -> Optional[Dict]:
        """Get information about KDE screen setup"""
        if not self.is_kde or not PYQT_AVAILABLE:
            return None
        
        try:
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import QRect
            
            # Create QApplication instance if it doesn't exist
            if not QApplication.instance():
                app = QApplication([])
            
            screen_count = QApplication.desktop().screenCount()
            primary_screen = QApplication.desktop().primaryScreen()
            
            monitors = []
            for i in range(screen_count):
                geometry = QApplication.desktop().screenGeometry(i)
                monitor_info = {
                    'index': i,
                    'name': f"Screen {i+1}",
                    'geometry': {
                        'x': geometry.x(),
                        'y': geometry.y(),
                        'width': geometry.width(),
                        'height': geometry.height()
                    },
                    'is_primary': (i == primary_screen)
                }
                monitors.append(monitor_info)
            
            return {
                'primary_monitor': primary_screen,
                'monitors': monitors
            }
            
        except Exception as e:
            logger.error(f"Error getting KDE screen info: {e}")
            return None
    
    def show_notification(self, title: str, message: str) -> bool:
        """Show a KDE notification"""
        if not self.is_kde:
            return False
        
        try:
            # Try using KDE's notification system via DBus
            if PYQT_AVAILABLE and self.dbus_connection.isConnected():
                notification_interface = QDBusInterface(
                    "org.freedesktop.Notifications",
                    "/org/freedesktop/Notifications",
                    "org.freedesktop.Notifications",
                    self.dbus_connection
                )
                
                if notification_interface.isValid():
                    notification_interface.call(
                        "Notify",
                        "ManjCast",          # App name
                        0,                   # Replaces ID
                        "video-display",     # Icon
                        title,               # Summary
                        message,             # Body
                        [],                  # Actions
                        {},                  # Hints
                        5000                 # Timeout (5 seconds)
                    )
                    return True
            
            # Fall back to notify-send
            subprocess.run([
                "notify-send",
                "--icon=video-display",
                title,
                message
            ])
            return True
                
        except Exception as e:
            logger.error(f"Error showing KDE notification: {e}")
            return False
