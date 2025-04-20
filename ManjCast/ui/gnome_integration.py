#!/usr/bin/env python3
# ManjCast - Screen Casting Tool for Manjaro Linux
# GNOME Desktop Environment Integration

import os
import logging
import subprocess
import gi
try:
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Gdk
    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False

logger = logging.getLogger("ManjCast.UI.GnomeIntegration")

class GnomeIntegration:
    """Provides integration with GNOME desktop environment"""
    
    def __init__(self):
        self.is_gnome = self._check_if_gnome()
    
    def _check_if_gnome(self) -> bool:
        """Check if running in a GNOME session"""
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        if "gnome" in desktop:
            return True
        
        # Alternative check
        try:
            output = subprocess.check_output(["ps", "-e"]).decode()
            if "gnome-shell" in output:
                return True
        except Exception as e:
            logger.error(f"Error checking for GNOME: {e}")
        
        return False
    
    def setup_indicator(self, callback):
        """Set up a GNOME indicator/app indicator"""
        if not self.is_gnome or not GTK_AVAILABLE:
            logger.warning("Cannot set up GNOME indicator - not running in GNOME or GTK not available")
            return False
        
        try:
            # Try to use AppIndicator3 if available
            try:
                gi.require_version('AppIndicator3', '0.1')
                from gi.repository import AppIndicator3
                
                indicator = AppIndicator3.Indicator.new(
                    "manjcast-indicator",
                    "video-display",
                    AppIndicator3.IndicatorCategory.APPLICATION_STATUS
                )
                indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
                
                # Create menu
                menu = Gtk.Menu()
                
                # Add menu items
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
                indicator.set_menu(menu)
                
                logger.info("GNOME AppIndicator set up successfully")
                return True
                
            except (ImportError, ValueError):
                logger.warning("AppIndicator3 not available, falling back to StatusIcon")
                
                # Fall back to StatusIcon
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
                
                icon.connect("popup-menu", self._show_menu, menu)
                icon.connect("activate", lambda _: callback("show"))
                
                logger.info("GNOME StatusIcon set up successfully")
                return True
            
        except Exception as e:
            logger.error(f"Error setting up GNOME indicator: {e}")
            return False
    
    def _show_menu(self, icon, button, time, menu):
        """Show the popup menu for the StatusIcon"""
        menu.popup(None, None, Gtk.StatusIcon.position_menu, icon, button, time)
    
    def setup_autostart(self, enable: bool = True) -> bool:
        """Set up or remove autostart entry for GNOME"""
        if not self.is_gnome:
            logger.warning("Cannot set up GNOME autostart - not running in GNOME")
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
Categories=GNOME;GTK;Utility;
AutostartCondition=GSettings org.gnome.desktop.background show-desktop-icons
X-GNOME-Autostart-enabled=true
""")
                logger.info("GNOME autostart enabled")
                return True
                
            else:
                # Remove autostart entry if it exists
                if os.path.exists(autostart_file):
                    os.remove(autostart_file)
                    logger.info("GNOME autostart disabled")
                return True
                
        except Exception as e:
            logger.error(f"Error setting up GNOME autostart: {e}")
            return False
    
    def get_current_workspace(self) -> int:
        """Get the current GNOME workspace number"""
        if not self.is_gnome:
            return 0
        
        try:
            # Try to use GSettings to get the current workspace
            output = subprocess.check_output([
                "gsettings", "get", "org.gnome.desktop.wm.preferences", "current-workspace"
            ]).decode().strip()
            
            # Parse the output (should be a number)
            try:
                workspace = int(output)
                return workspace
            except ValueError:
                pass
            
            # Alternative method using wmctrl
            try:
                output = subprocess.check_output(["wmctrl", "-d"]).decode()
                for line in output.split('\n'):
                    if '*' in line:  # Current workspace is marked with *
                        parts = line.split()
                        if parts:
                            return int(parts[0])
            except:
                pass
                
        except Exception as e:
            logger.error(f"Error getting current GNOME workspace: {e}")
        
        return 0
    
    def get_screen_info(self):
        """Get information about GNOME screen setup"""
        if not self.is_gnome or not GTK_AVAILABLE:
            return None
        
        try:
            # Use modern Gtk/Gdk API for GTK3
            display = Gdk.Display.get_default()
            if display is None:
                logger.error("No display available")
                return None
            
            # Get the primary monitor
            monitor_count = display.get_n_monitors()
            primary_monitor = display.get_primary_monitor()
            
            # Collect information about all monitors
            monitors = []
            for i in range(monitor_count):
                monitor = display.get_monitor(i)
                geometry = monitor.get_geometry()
                
                # Get monitor name (try various methods)
                try:
                    monitor_name = monitor.get_model()
                except:
                    try:
                        monitor_name = f"Monitor {i}"
                    except:
                        monitor_name = "Unknown"
                
                monitors.append({
                    'index': i,
                    'name': monitor_name,
                    'geometry': {
                        'x': geometry.x,
                        'y': geometry.y,
                        'width': geometry.width,
                        'height': geometry.height
                    },
                    'is_primary': (i == primary_monitor.get_monitor_num() if primary_monitor else False)
                })
            
            return {
                'primary_monitor': primary_monitor.get_monitor_num() if primary_monitor else 0,
                'monitors': monitors
            }
            
        except Exception as e:
            logger.error(f"Error getting GNOME screen info: {e}")
            return None
    
    def show_notification(self, title: str, message: str) -> bool:
        """Show a GNOME notification"""
        if not self.is_gnome:
            return False
        
        try:
            # Try using libnotify
            try:
                gi.require_version('Notify', '0.7')
                from gi.repository import Notify
                
                if not getattr(self, '_notify_initialized', False):
                    Notify.init("ManjCast")
                    self._notify_initialized = True
                
                notification = Notify.Notification.new(title, message, "video-display")
                notification.show()
                return True
                
            except (ImportError, ValueError):
                # Fall back to using notify-send
                subprocess.run([
                    "notify-send",
                    "--icon=video-display",
                    title,
                    message
                ])
                return True
                
        except Exception as e:
            logger.error(f"Error showing GNOME notification: {e}")
            return False
