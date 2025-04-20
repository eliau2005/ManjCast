#!/usr/bin/env python3
# ManjCast - Screen Casting Tool for Manjaro Linux
# XFCE Desktop Environment Integration

import os
import logging
import subprocess
from typing import Optional, Dict, Callable

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False

logger = logging.getLogger("ManjCast.UI.XfceIntegration")

class XfceIntegration:
    """Provides integration with XFCE desktop environment"""
    
    def __init__(self):
        self.is_xfce = self._check_if_xfce()
    
    def _check_if_xfce(self) -> bool:
        """Check if running in an XFCE session"""
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        if "xfce" in desktop:
            return True
        
        # Alternative check
        try:
            output = subprocess.check_output(["ps", "-e"]).decode()
            if "xfwm4" in output or "xfce" in output:
                return True
        except Exception as e:
            logger.error(f"Error checking for XFCE: {e}")
        
        return False
    
    def setup_indicator(self, callback: Callable) -> bool:
        """Set up an XFCE indicator/status icon"""
        if not self.is_xfce or not GTK_AVAILABLE:
            logger.warning("Cannot set up XFCE indicator - not running in XFCE or GTK not available")
            return False
        
        try:
            # XFCE uses GTK StatusIcon, similar to GNOME
            icon = Gtk.StatusIcon()
            icon.set_from_icon_name("video-display")
            icon.set_tooltip_text("ManjCast")
            
            # Create popup menu
            menu = Gtk.Menu()
            
            show_item = Gtk.MenuItem(label="Show ManjCast")
            show_item.connect("activate", lambda _: callback("show"))
            menu.append(show_item)
            
            menu.append(Gtk.SeparatorMenuItem())
            
            cast_item = Gtk.MenuItem(label="Start Casting")
            cast_item.connect("activate", lambda _: callback("cast"))
            menu.append(cast_item)
            
            stop_item = Gtk.MenuItem(label="Stop Casting")
            stop_item.connect("activate", lambda _: callback("stop"))
            menu.append(stop_item)
            
            menu.append(Gtk.SeparatorMenuItem())
            
            quit_item = Gtk.MenuItem(label="Quit")
            quit_item.connect("activate", lambda _: callback("quit"))
            menu.append(quit_item)
            
            menu.show_all()
            
            # Connect signals
            icon.connect("popup-menu", self._show_menu, menu)
            icon.connect("activate", lambda _: callback("show"))
            
            logger.info("XFCE StatusIcon set up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up XFCE indicator: {e}")
            return False
    
    def _show_menu(self, icon, button, time, menu):
        """Show the popup menu for the StatusIcon"""
        menu.popup(None, None, Gtk.StatusIcon.position_menu, icon, button, time)
    
    def setup_autostart(self, enable: bool = True) -> bool:
        """Set up or remove autostart entry for XFCE"""
        if not self.is_xfce:
            logger.warning("Cannot set up XFCE autostart - not running in XFCE")
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
Categories=GTK;XFCE;Utility;
StartupNotify=true
X-XFCE-Source=file:///usr/bin/manjcast
""")
                logger.info("XFCE autostart enabled")
                return True
                
            else:
                # Remove autostart entry if it exists
                if os.path.exists(autostart_file):
                    os.remove(autostart_file)
                    logger.info("XFCE autostart disabled")
                return True
                
        except Exception as e:
            logger.error(f"Error setting up XFCE autostart: {e}")
            return False
    
    def get_current_workspace(self) -> int:
        """Get the current XFCE workspace number"""
        if not self.is_xfce:
            return 0
        
        try:
            # Try using xfconf-query for XFCE-specific information
            output = subprocess.check_output([
                "xfconf-query", 
                "-c", "xfwm4", 
                "-p", "/general/workspace_count"
            ]).decode().strip()
            
            # Parse the output
            try:
                workspace_count = int(output)
                
                # Now get current workspace
                try:
                    # XFCE stores current workspace info in xfwm4
                    current_output = subprocess.check_output([
                        "xfconf-query", 
                        "-c", "xfwm4", 
                        "-p", "/general/workspace_names"
                    ]).decode().strip()
                    
                    # If we got this far but couldn't parse, fall back to wmctrl
                    return self._get_workspace_from_wmctrl()
                    
                except:
                    return self._get_workspace_from_wmctrl()
                    
            except ValueError:
                return self._get_workspace_from_wmctrl()
                
        except Exception as e:
            logger.error(f"Error getting XFCE workspace info: {e}")
            return self._get_workspace_from_wmctrl()
    
    def _get_workspace_from_wmctrl(self) -> int:
        """Helper method to get current workspace using wmctrl"""
        try:
            output = subprocess.check_output(["wmctrl", "-d"]).decode()
            for line in output.split('\n'):
                if '*' in line:  # Current workspace is marked with *
                    parts = line.split()
                    if parts:
                        return int(parts[0])
        except Exception as e:
            logger.error(f"Error getting workspace with wmctrl: {e}")
        
        return 0
    
    def get_screen_info(self) -> Optional[Dict]:
        """Get information about XFCE screen setup"""
        if not self.is_xfce or not GTK_AVAILABLE:
            return None
        
        try:
            from gi.repository import Gdk
            
            # Get display information
            display = Gdk.Display.get_default()
            if display is None:
                logger.error("No display available")
                return None
            
            # Get monitor information
            monitors = []
            n_monitors = display.get_n_monitors()
            
            primary_monitor_num = None
            for i in range(n_monitors):
                monitor = display.get_monitor(i)
                geometry = monitor.get_geometry()
                
                # Is this the primary monitor?
                is_primary = monitor.is_primary()
                if is_primary:
                    primary_monitor_num = i
                
                # Try to get the monitor name
                monitor_name = "Unknown"
                try:
                    monitor_name = monitor.get_model()
                except:
                    monitor_name = f"Monitor {i+1}"
                
                # Create monitor info object
                monitor_info = {
                    'index': i,
                    'name': monitor_name,
                    'geometry': {
                        'x': geometry.x,
                        'y': geometry.y,
                        'width': geometry.width,
                        'height': geometry.height
                    },
                    'is_primary': is_primary
                }
                monitors.append(monitor_info)
            
            return {
                'primary_monitor': primary_monitor_num if primary_monitor_num is not None else 0,
                'monitors': monitors
            }
            
        except Exception as e:
            logger.error(f"Error getting XFCE screen info: {e}")
            return None
    
    def show_notification(self, title: str, message: str) -> bool:
        """Show an XFCE notification"""
        if not self.is_xfce:
            return False
        
        try:
            # Use xfce4-notifyd if available (via notify-send)
            subprocess.run([
                "notify-send",
                "--icon=video-display",
                title,
                message
            ])
            return True
                
        except Exception as e:
            logger.error(f"Error showing XFCE notification: {e}")
            return False
