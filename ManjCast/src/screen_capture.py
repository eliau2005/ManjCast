#!/usr/bin/env python3
# ManjCast - Screen Casting Tool for Manjaro Linux
# Screen Capture Module

import logging
import subprocess
import os
import time
import threading
import re
from typing import Optional, Tuple, List, Dict, Any

logger = logging.getLogger("ManjCast.ScreenCapture")

class ScreenCapture:
    """Handles capturing the screen or a specific window for casting"""
    
    def __init__(self, config):
        self.config = config
        self.display = os.environ.get("DISPLAY", ":0")
        self.is_capturing = False
        self.capture_process = None
        self.desktop_environment = self._detect_desktop_environment()
        self.screen_dimensions = self._get_screen_dimensions()
        self.window_list = {}  # Dictionary to store window IDs and titles
    
    def _detect_desktop_environment(self) -> str:
        """Detect the current desktop environment"""
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        
        if "kde" in desktop:
            return "kde"
        elif "gnome" in desktop:
            return "gnome"
        elif "xfce" in desktop:
            return "xfce"
        else:
            # Try to detect based on process list
            try:
                processes = subprocess.check_output(["ps", "-e"]).decode()
                if "kwin" in processes or "plasma" in processes:
                    return "kde"
                elif "gnome-shell" in processes:
                    return "gnome" 
                elif "xfwm" in processes or "xfce" in processes:
                    return "xfce"
            except:
                pass
                
            # Default to a generic environment
            return "unknown"
    
    def _get_screen_dimensions(self) -> Tuple[int, int]:
        """Get the screen dimensions"""
        # First try: use config resolution if available
        config_resolution = self.config.get('CASTING', 'resolution', fallback='1080p')
        if config_resolution:
            if config_resolution == "1080p":
                return (1920, 1080)
            elif config_resolution == "720p":
                return (1280, 720)
            elif config_resolution == "480p":
                return (854, 480)
            elif "x" in config_resolution:
                # Parse WIDTHxHEIGHT format
                try:
                    width, height = config_resolution.split("x")
                    return (int(width), int(height))
                except (ValueError, IndexError):
                    pass
        
        # Second try: use xrandr if available
        try:
            output = subprocess.check_output(["xrandr"], stderr=subprocess.PIPE).decode()
            # Look for the current resolution
            match = re.search(r'current (\d+) x (\d+)', output)
            if match:
                width = int(match.group(1))
                height = int(match.group(2))
                return (width, height)
            
            # If that fails, try another method
            for line in output.split('\n'):
                if '*' in line:  # Current resolution marked with *
                    match = re.search(r'(\d+)x(\d+)', line)
                    if match:
                        width = int(match.group(1))
                        height = int(match.group(2))
                        return (width, height)
        except Exception as e:
            logger.error(f"Error getting screen dimensions with xrandr: {e}")
        
        # Third try: try to get from PyQt if desktop environment is available
        try:
            if self.desktop_environment in ["kde", "gnome", "xfce"]:
                if self.desktop_environment == "kde":
                    # Try with Qt
                    from PyQt5.QtWidgets import QApplication
                    app = QApplication.instance() or QApplication([])
                    screen = app.primaryScreen()
                    size = screen.size()
                    return (size.width(), size.height())
                elif self.desktop_environment in ["gnome", "xfce"]:
                    # Try with Gtk
                    import gi
                    gi.require_version('Gtk', '3.0')
                    from gi.repository import Gtk, Gdk
                    display = Gdk.Display.get_default()
                    if display:
                        monitor = display.get_primary_monitor() or display.get_monitor(0)
                        if monitor:
                            geometry = monitor.get_geometry()
                            return (geometry.width, geometry.height)
        except Exception as e:
            logger.error(f"Error getting screen dimensions with desktop API: {e}")
        
        # Fourth try: use Wayland-specific methods if we're on Wayland
        wayland_session = os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
        if wayland_session:
            try:
                # Try to get from sway or other Wayland compositors
                output = subprocess.check_output(["wlr-randr"], stderr=subprocess.PIPE).decode()
                match = re.search(r'(\d+)x(\d+)', output)
                if match:
                    width = int(match.group(1))
                    height = int(match.group(2))
                    return (width, height)
            except Exception:
                pass
        
        # Last resort: Return a default resolution if all else fails
        # Using 1920x1080 as a common default resolution
        logger.warning("Could not detect screen resolution, using default 1920x1080")
        return (1920, 1080)
    
    def get_window_list(self) -> dict:
        """Get a list of open windows that can be captured"""
        window_list = {}
        
        try:
            # Try using xwininfo to list all windows
            output = subprocess.check_output(
                ["xwininfo", "-tree", "-root"], 
                stderr=subprocess.PIPE
            ).decode()
            
            # Parse the output to get window IDs and titles
            lines = output.split('\n')
            for line in lines:
                # Look for window IDs and names
                match = re.search(r'(0x[0-9a-f]+) "([^"]+)"', line)
                if match:
                    window_id = match.group(1)
                    window_title = match.group(2)
                    
                    # Filter out some system windows
                    if (window_title and 
                        not window_title.startswith("Desktop") and 
                        " - " in window_title):
                        window_list[window_id] = window_title
            
            # Alternative method using wmctrl if available
            if not window_list:
                try:
                    output = subprocess.check_output(["wmctrl", "-l"]).decode()
                    lines = output.split('\n')
                    for line in lines:
                        parts = line.split(None, 3)
                        if len(parts) >= 4:
                            window_id = parts[0]
                            window_title = parts[3]
                            window_list[window_id] = window_title
                except:
                    pass
            
            self.window_list = window_list
            return window_list
        
        except Exception as e:
            logger.error(f"Error getting window list: {e}")
            
            # Fallback for when X11 tools aren't available
            # Try to at least get one generic entry for the whole desktop
            window_list["desktop"] = "Full Desktop"
            self.window_list = window_list
            return window_list
    
    def get_display(self) -> str:
        """Get the X display identifier"""
        return self.display
    
    def start_capture(self, window_id: Optional[str] = None) -> bool:
        """Start screen capture. If window_id is provided, capture only that window"""
        if self.is_capturing:
            logger.warning("Screen capture is already running")
            return False
        
        try:
            # Nothing to start here - the actual capture will be handled by ffmpeg
            # in the cast_manager module. This method just updates the state and
            # performs any necessary preparations.
            
            if window_id:
                # Skip verification if window_id is "desktop" (our fallback)
                if window_id != "desktop" and window_id not in self.get_window_list():
                    logger.error(f"Window with ID {window_id} not found")
                    return False
                logger.info(f"Starting capture of window {window_id}")
            else:
                logger.info("Starting full screen capture")
            
            self.is_capturing = True
            return True
            
        except Exception as e:
            logger.error(f"Error starting screen capture: {e}")
            self.is_capturing = False
            return False
    
    def stop_capture(self):
        """Stop screen capture"""
        if not self.is_capturing:
            return
        
        try:
            # Clean up any resources if needed
            if self.capture_process and self.capture_process.poll() is None:
                self.capture_process.terminate()
                try:
                    self.capture_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.capture_process.kill()
                
            self.is_capturing = False
            logger.info("Screen capture stopped")
            
        except Exception as e:
            logger.error(f"Error stopping screen capture: {e}")
    
    def get_active_window(self) -> Optional[str]:
        """Get the ID of the currently active window"""
        try:
            # Try xdotool first
            try:
                window_id = subprocess.check_output(
                    ["xdotool", "getactivewindow"]
                ).decode().strip()
                return window_id
            except:
                pass
            
            # Try wmctrl next
            try:
                output = subprocess.check_output(
                    ["wmctrl", "-a", ":ACTIVE:"]
                ).decode()
                # Parse output to get window ID
                match = re.search(r'(0x[0-9a-f]+)', output)
                if match:
                    return match.group(1)
            except:
                pass
            
            # Fallback for non-X11 environments
            return "desktop"
                
        except Exception as e:
            logger.error(f"Error getting active window: {e}")
        
        return None
    
    def get_window_position(self, window_id: str) -> Optional[Tuple[int, int, int, int]]:
        """Get the position and size of a window (x, y, width, height)"""
        # Fallback for non-X11 environments
        if window_id == "desktop":
            return (0, 0, self.screen_dimensions[0], self.screen_dimensions[1])
            
        try:
            # Try using xwininfo to get window geometry
            output = subprocess.check_output(
                ["xwininfo", "-id", window_id]
            ).decode()
            
            # Parse the output to get position and dimensions
            x = y = width = height = None
            
            for line in output.split('\n'):
                if "Absolute upper-left X:" in line:
                    x = int(line.split(':')[1].strip())
                elif "Absolute upper-left Y:" in line:
                    y = int(line.split(':')[1].strip())
                elif "Width:" in line:
                    width = int(line.split(':')[1].strip())
                elif "Height:" in line:
                    height = int(line.split(':')[1].strip())
            
            if x is not None and y is not None and width is not None and height is not None:
                return (x, y, width, height)
                
        except Exception as e:
            logger.error(f"Error getting window position: {e}")
        
        return None
