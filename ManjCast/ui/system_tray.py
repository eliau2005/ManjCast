#!/usr/bin/env python3
# ManjCast - Screen Casting Tool for Manjaro Linux
# System Tray Icon

import os
import logging
from PyQt5.QtWidgets import (
    QSystemTrayIcon, QMenu, QAction, QWidget, 
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QApplication
)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, pyqtSlot

logger = logging.getLogger("ManjCast.UI.SystemTray")

class SystemTrayIcon(QSystemTrayIcon):
    """System tray icon for ManjCast"""
    
    def __init__(self, main_window, cast_manager):
        super().__init__()
        
        self.main_window = main_window
        self.cast_manager = cast_manager
        
        # Create the tray icon
        self.setup_icon()
        
        # Create the tray menu
        self.setup_menu()
        
        # Connect signals
        self.activated.connect(self.on_activated)
        
        # Register for cast status updates
        self.cast_manager.register_status_callback(self.update_status)
    
    def setup_icon(self):
        """Set up the tray icon"""
        # Check for icon in several locations
        icon_paths = [
            # From installation
            "/usr/share/icons/hicolor/scalable/apps/manjcast.svg",
            "/usr/share/icons/hicolor/128x128/apps/manjcast.png",
            # From project directory
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                        "assets/manjcast.png"),
            # Fallback to system icon
            "/usr/share/icons/hicolor/128x128/apps/video-display.png",
        ]
        
        icon = None
        for path in icon_paths:
            if os.path.exists(path):
                icon = QIcon(path)
                break
        
        # If no icon found, create a fallback icon
        if not icon:
            # Create a simple pixmap as fallback
            pixmap = QPixmap(128, 128)
            pixmap.fill(Qt.blue)
            icon = QIcon(pixmap)
            
        self.setIcon(icon)
        self.setToolTip("ManjCast - Screen Casting for Manjaro")
    
    def setup_menu(self):
        """Set up the tray menu"""
        self.menu = QMenu()
        
        # Main window action
        self.show_window_action = QAction("Show ManjCast", self)
        self.show_window_action.triggered.connect(self.show_main_window)
        self.menu.addAction(self.show_window_action)
        
        self.menu.addSeparator()
        
        # Quick cast submenu
        self.quick_cast_menu = QMenu("Quick Cast", self.menu)
        
        # Full screen action
        self.cast_screen_action = QAction("Cast Full Screen", self)
        self.cast_screen_action.triggered.connect(self.quick_cast_screen)
        self.quick_cast_menu.addAction(self.cast_screen_action)
        
        # Active window action
        self.cast_window_action = QAction("Cast Active Window", self)
        self.cast_window_action.triggered.connect(self.quick_cast_window)
        self.quick_cast_menu.addAction(self.cast_window_action)
        
        # Custom cast action
        self.custom_cast_action = QAction("Custom Cast...", self)
        self.custom_cast_action.triggered.connect(self.show_custom_cast_dialog)
        self.quick_cast_menu.addAction(self.custom_cast_action)
        
        self.menu.addMenu(self.quick_cast_menu)
        
        # Stop casting action
        self.stop_action = QAction("Stop Casting", self)
        self.stop_action.triggered.connect(self.stop_casting)
        self.stop_action.setEnabled(False)
        self.menu.addAction(self.stop_action)
        
        self.menu.addSeparator()
        
        # Quit action
        self.quit_action = QAction("Quit", self)
        self.quit_action.triggered.connect(self.quit_application)
        self.menu.addAction(self.quit_action)
        
        # Set the menu
        self.setContextMenu(self.menu)
    
    def update_status(self, status):
        """Update the tray icon and menu based on casting status"""
        if status == "started":
            # Update icon for casting state
            # (We could use a different icon here if available)
            self.setToolTip("ManjCast - Currently Casting")
            
            # Enable/disable menu items
            self.cast_screen_action.setEnabled(False)
            self.cast_window_action.setEnabled(False)
            self.custom_cast_action.setEnabled(False)
            self.stop_action.setEnabled(True)
            
        elif status in ["stopped", "error", "disconnected"]:
            # Restore normal icon
            self.setup_icon()
            self.setToolTip("ManjCast - Screen Casting for Manjaro")
            
            # Enable/disable menu items
            self.cast_screen_action.setEnabled(True)
            self.cast_window_action.setEnabled(True)
            self.custom_cast_action.setEnabled(True)
            self.stop_action.setEnabled(False)
    
    @pyqtSlot(QSystemTrayIcon.ActivationReason)
    def on_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_main_window()
        elif reason == QSystemTrayIcon.Trigger:
            # On single click, show a notification with current status
            if self.cast_manager.is_casting:
                device_name = "Unknown device"
                if self.cast_manager.current_device:
                    device_name = self.cast_manager.current_device.device.friendly_name
                
                self.showMessage(
                    "ManjCast Status",
                    f"Currently casting to: {device_name}",
                    QSystemTrayIcon.Information,
                    3000
                )
    
    @pyqtSlot()
    def show_main_window(self):
        """Show the main application window"""
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
    
    @pyqtSlot()
    def quick_cast_screen(self):
        """Quick cast the full screen"""
        # If no device is selected yet, show the custom dialog
        if not self.cast_manager.current_device:
            self.show_custom_cast_dialog()
            return
        
        # Set casting mode
        self.cast_manager.set_cast_mode("screen")
        
        # Enable audio by default
        self.cast_manager.set_audio_enabled(True)
        
        # Start casting
        success = self.cast_manager.start_casting()
        if success:
            self.showMessage(
                "ManjCast",
                "Started casting full screen",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            self.showMessage(
                "ManjCast Error",
                "Failed to start casting",
                QSystemTrayIcon.Critical,
                3000
            )
    
    @pyqtSlot()
    def quick_cast_window(self):
        """Quick cast the active window"""
        # If no device is selected yet, show the custom dialog
        if not self.cast_manager.current_device:
            self.show_custom_cast_dialog()
            return
            
        # Get the active window ID
        window_id = self.cast_manager.screen_capture.get_active_window()
        if not window_id:
            self.showMessage(
                "ManjCast Error",
                "Failed to detect active window",
                QSystemTrayIcon.Warning,
                3000
            )
            return
        
        # Set casting mode
        self.cast_manager.set_cast_mode("window", window_id)
        
        # Enable audio by default
        self.cast_manager.set_audio_enabled(True)
        
        # Start casting
        success = self.cast_manager.start_casting()
        if success:
            self.showMessage(
                "ManjCast",
                "Started casting active window",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            self.showMessage(
                "ManjCast Error",
                "Failed to start casting",
                QSystemTrayIcon.Critical,
                3000
            )
    
    @pyqtSlot()
    def show_custom_cast_dialog(self):
        """Show a dialog for custom casting options"""
        dialog = CustomCastDialog(self.cast_manager, self.main_window)
        dialog.exec_()
    
    @pyqtSlot()
    def stop_casting(self):
        """Stop the current casting session"""
        self.cast_manager.stop_casting()
        self.showMessage(
            "ManjCast",
            "Casting stopped",
            QSystemTrayIcon.Information,
            2000
        )
    
    @pyqtSlot()
    def quit_application(self):
        """Quit the application"""
        # Stop casting and clean up
        self.cast_manager.stop_casting()
        
        # Quit the application
        QApplication.quit()


class CustomCastDialog(QDialog):
    """Dialog for customizing casting options"""
    
    def __init__(self, cast_manager, parent=None):
        super().__init__(parent)
        
        self.cast_manager = cast_manager
        self.device_discovery = None
        
        # Get access to the device discovery module
        # This is a circular import, but we only need it here
        from src.device_discovery import DeviceDiscovery
        self.device_discovery = DeviceDiscovery(self.cast_manager)
        
        # Initialize UI
        self.init_ui()
        
        # Start device discovery
        self.device_discovery.start_discovery()
        self.device_discovery.register_callback(self.update_device_list)
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Quick Cast")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Device selection
        device_layout = QHBoxLayout()
        device_label = QLabel("Cast to:")
        device_layout.addWidget(device_label)
        
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(250)
        device_layout.addWidget(self.device_combo)
        
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_devices)
        device_layout.addWidget(refresh_button)
        
        layout.addLayout(device_layout)
        
        # Casting options
        options_layout = QVBoxLayout()
        options_label = QLabel("Cast Options:")
        options_layout.addWidget(options_label)
        
        # Screen option
        self.screen_radio = QRadioButton("Full Screen")
        self.screen_radio.setChecked(True)
        options_layout.addWidget(self.screen_radio)
        
        # Window option
        window_layout = QHBoxLayout()
        self.window_radio = QRadioButton("Window:")
        window_layout.addWidget(self.window_radio)
        
        self.window_combo = QComboBox()
        self.window_combo.setEnabled(False)
        window_layout.addWidget(self.window_combo)
        
        options_layout.addLayout(window_layout)
        
        # Audio option
        self.audio_checkbox = QCheckBox("Include Audio")
        self.audio_checkbox.setChecked(True)
        options_layout.addWidget(self.audio_checkbox)
        
        layout.addLayout(options_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        cast_button = QPushButton("Start Casting")
        cast_button.clicked.connect(self.start_casting)
        button_layout.addWidget(cast_button)
        
        layout.addLayout(button_layout)
        
        # Connect signals
        self.window_radio.toggled.connect(self.on_window_radio_toggled)
        
        # Load window list
        self.update_window_list()
    
    def update_device_list(self, devices):
        """Update the device list with discovered devices"""
        self.device_combo.clear()
        
        for uuid, device in devices.items():
            item_text = f"{device['name']} ({device['model_name']})"
            self.device_combo.addItem(item_text, userData=uuid)
    
    def update_window_list(self):
        """Update the window list"""
        self.window_combo.clear()
        
        # Get window list
        windows = self.cast_manager.screen_capture.get_window_list()
        
        for window_id, window_title in windows.items():
            self.window_combo.addItem(window_title, userData=window_id)
    
    def refresh_devices(self):
        """Refresh the device list"""
        self.device_discovery.stop_discovery()
        self.device_discovery.start_discovery()
    
    def on_window_radio_toggled(self, checked):
        """Enable/disable window selection based on radio button state"""
        self.window_combo.setEnabled(checked)
    
    def start_casting(self):
        """Start casting with the selected options"""
        # Check if a device is selected
        if self.device_combo.currentIndex() < 0:
            self.parent().showMessage(
                "ManjCast Error",
                "Please select a device",
                QSystemTrayIcon.Warning,
                3000
            )
            return
        
        # Select the device
        device_uuid = self.device_combo.currentData()
        success = self.cast_manager.select_device(device_uuid)
        if not success:
            self.parent().showMessage(
                "ManjCast Error",
                "Failed to connect to the selected device",
                QSystemTrayIcon.Critical,
                3000
            )
            return
        
        # Set casting mode
        if self.window_radio.isChecked():
            if self.window_combo.currentIndex() < 0:
                self.parent().showMessage(
                    "ManjCast Error",
                    "Please select a window",
                    QSystemTrayIcon.Warning,
                    3000
                )
                return
                
            window_id = self.window_combo.currentData()
            self.cast_manager.set_cast_mode("window", window_id)
        else:
            self.cast_manager.set_cast_mode("screen")
        
        # Set audio option
        self.cast_manager.set_audio_enabled(self.audio_checkbox.isChecked())
        
        # Start casting
        success = self.cast_manager.start_casting()
        if success:
            self.parent().showMessage(
                "ManjCast",
                "Started casting",
                QSystemTrayIcon.Information,
                2000
            )
            self.accept()
        else:
            self.parent().showMessage(
                "ManjCast Error",
                "Failed to start casting",
                QSystemTrayIcon.Critical,
                3000
            )
    
    def closeEvent(self, event):
        """Clean up when dialog is closed"""
        # Stop device discovery
        if self.device_discovery:
            self.device_discovery.unregister_callback(self.update_device_list)
            self.device_discovery.stop_discovery()
        
        event.accept()
