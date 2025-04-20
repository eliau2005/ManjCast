#!/usr/bin/env python3
# ManjCast - Screen Casting Tool for Manjaro Linux
# Main Window UI

import os
import sys
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QTabWidget,
    QRadioButton, QComboBox, QCheckBox, QGroupBox, QFormLayout,
    QSpinBox, QTextEdit, QSplitter, QMessageBox, QFrame
)
from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtCore import Qt, pyqtSlot, QSize

logger = logging.getLogger("ManjCast.UI.MainWindow")

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, cast_manager, device_discovery):
        super().__init__()
        
        self.cast_manager = cast_manager
        self.device_discovery = device_discovery
        
        # Set up UI
        self.init_ui()
        
        # Register for device updates
        self.device_discovery.register_callback(self.update_device_list)
        
        # Register for cast status updates
        self.cast_manager.register_status_callback(self.update_cast_status)
        
        # Check for Wayland session
        self.is_wayland = os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
        if self.is_wayland:
            logger.warning("Running under Wayland - some screen capture features may be limited")
            self.show_wayland_warning()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("ManjCast")
        self.setMinimumSize(800, 600)
        
        # Set window icon
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets/manjcast.png"
        )
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.cast_tab = self.create_cast_tab()
        self.settings_tab = self.create_settings_tab()
        self.about_tab = self.create_about_tab()
        
        # Add tabs to the tab widget
        self.tab_widget.addTab(self.cast_tab, "Cast")
        self.tab_widget.addTab(self.settings_tab, "Settings")
        self.tab_widget.addTab(self.about_tab, "About")
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Update UI state
        self.update_ui_state()
    
    def create_cast_tab(self):
        """Create the casting tab"""
        cast_widget = QWidget()
        cast_layout = QHBoxLayout(cast_widget)
        
        # Left side - Device list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        devices_group = QGroupBox("Available Devices")
        devices_layout = QVBoxLayout(devices_group)
        
        self.device_list = QListWidget()
        self.device_list.setMinimumWidth(200)
        self.device_list.itemClicked.connect(self.on_device_selected)
        devices_layout.addWidget(self.device_list)
        
        refresh_button = QPushButton("Refresh Devices")
        refresh_button.clicked.connect(self.on_refresh_devices)
        devices_layout.addWidget(refresh_button)
        
        left_layout.addWidget(devices_group)
        
        # Right side - Casting options
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Cast mode group
        cast_mode_group = QGroupBox("Cast Mode")
        cast_mode_layout = QVBoxLayout(cast_mode_group)
        
        # Screen mode
        self.screen_radio = QRadioButton("Full Screen")
        self.screen_radio.setChecked(True)
        self.screen_radio.toggled.connect(self.on_cast_mode_changed)
        cast_mode_layout.addWidget(self.screen_radio)
        
        # Window mode
        window_layout = QHBoxLayout()
        self.window_radio = QRadioButton("Application Window:")
        self.window_radio.toggled.connect(self.on_cast_mode_changed)
        window_layout.addWidget(self.window_radio)
        
        self.window_combo = QComboBox()
        self.window_combo.setEnabled(False)
        window_layout.addWidget(self.window_combo)
        
        refresh_windows_button = QPushButton("Refresh")
        refresh_windows_button.clicked.connect(self.update_window_list)
        window_layout.addWidget(refresh_windows_button)
        
        cast_mode_layout.addLayout(window_layout)
        right_layout.addWidget(cast_mode_group)
        
        # Audio options
        audio_group = QGroupBox("Audio Options")
        audio_layout = QVBoxLayout(audio_group)
        
        self.audio_checkbox = QCheckBox("Include Audio")
        self.audio_checkbox.setChecked(True)
        self.audio_checkbox.stateChanged.connect(self.on_audio_option_changed)
        audio_layout.addWidget(self.audio_checkbox)
        
        right_layout.addWidget(audio_group)
        
        # Wayland warning (only shown if on Wayland)
        if self.is_wayland:
            wayland_warning = QGroupBox("Wayland Session Detected")
            wayland_layout = QVBoxLayout(wayland_warning)
            
            warning_label = QLabel(
                "You are running in a Wayland session. Screen casting may have limited functionality.\n"
                "For best results, consider logging in with an X11 session instead."
            )
            warning_label.setWordWrap(True)
            warning_label.setStyleSheet("color: #FF6700;")
            wayland_layout.addWidget(warning_label)
            
            right_layout.addWidget(wayland_warning)
        
        # Cast controls
        controls_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Casting")
        self.start_button.clicked.connect(self.on_start_casting)
        controls_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Casting")
        self.stop_button.clicked.connect(self.on_stop_casting)
        self.stop_button.setEnabled(False)
        controls_layout.addWidget(self.stop_button)
        
        right_layout.addLayout(controls_layout)
        
        # Status text
        self.status_label = QLabel("Not casting")
        self.status_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.status_label)
        
        # Add the splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([200, 600])
        
        cast_layout.addWidget(splitter)
        
        return cast_widget
    
    def create_settings_tab(self):
        """Create the settings tab"""
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        
        # General settings
        general_group = QGroupBox("General Settings")
        general_layout = QVBoxLayout(general_group)
        
        # Minimize to tray
        self.minimize_checkbox = QCheckBox("Minimize to System Tray")
        self.minimize_checkbox.setChecked(
            self.cast_manager.config.getboolean('GENERAL', 'minimize_to_tray', fallback=True)
        )
        self.minimize_checkbox.stateChanged.connect(self.on_minimize_changed)
        general_layout.addWidget(self.minimize_checkbox)
        
        # Start with system
        self.autostart_checkbox = QCheckBox("Start with System")
        self.autostart_checkbox.setChecked(
            self.cast_manager.config.getboolean('GENERAL', 'start_with_system', fallback=False)
        )
        self.autostart_checkbox.stateChanged.connect(self.on_autostart_changed)
        general_layout.addWidget(self.autostart_checkbox)
        
        settings_layout.addWidget(general_group)
        
        # Casting settings
        casting_group = QGroupBox("Casting Settings")
        casting_layout = QFormLayout(casting_group)
        
        # Resolution
        self.resolution_combo = QComboBox()
        resolutions = ["1080p", "720p", "480p", "Custom..."]
        self.resolution_combo.addItems(resolutions)
        
        current_resolution = self.cast_manager.config.get('CASTING', 'resolution', fallback='1080p')
        if current_resolution in resolutions:
            self.resolution_combo.setCurrentText(current_resolution)
        else:
            self.resolution_combo.setCurrentText("Custom...")
            # TODO: Add custom resolution handling
        
        self.resolution_combo.currentTextChanged.connect(self.on_resolution_changed)
        casting_layout.addRow("Resolution:", self.resolution_combo)
        
        # Framerate
        self.framerate_combo = QComboBox()
        framerates = ["30", "25", "24", "20", "15"]
        self.framerate_combo.addItems(framerates)
        
        current_framerate = self.cast_manager.config.get('CASTING', 'framerate', fallback='30')
        if current_framerate in framerates:
            self.framerate_combo.setCurrentText(current_framerate)
        else:
            self.framerate_combo.setCurrentText("30")
        
        self.framerate_combo.currentTextChanged.connect(self.on_framerate_changed)
        casting_layout.addRow("Framerate:", self.framerate_combo)
        
        settings_layout.addWidget(casting_group)
        
        # Advanced settings
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QFormLayout(advanced_group)
        
        # Discovery timeout
        self.timeout_combo = QComboBox()
        timeouts = ["3", "5", "8", "10", "15"]
        self.timeout_combo.addItems(timeouts)
        
        current_timeout = self.cast_manager.config.get('ADVANCED', 'discovery_timeout', fallback='5')
        if current_timeout in timeouts:
            self.timeout_combo.setCurrentText(current_timeout)
        else:
            self.timeout_combo.setCurrentText("5")
        
        self.timeout_combo.currentTextChanged.connect(self.on_timeout_changed)
        advanced_layout.addRow("Discovery Timeout (s):", self.timeout_combo)
        
        # Wayland specific settings if running on Wayland
        if self.is_wayland:
            wayland_frame = QFrame()
            wayland_frame.setFrameShape(QFrame.StyledPanel)
            wayland_frame.setFrameShadow(QFrame.Raised)
            wayland_layout = QVBoxLayout(wayland_frame)
            
            wayland_title = QLabel("Wayland Specific Settings")
            wayland_title.setStyleSheet("font-weight: bold;")
            wayland_layout.addWidget(wayland_title)
            
            wayland_info = QLabel(
                "When running under Wayland, ManjCast will try to use native screen capture methods if available.\n"
                "If screen casting doesn't work, you can try installing wf-recorder for improved Wayland support."
            )
            wayland_info.setWordWrap(True)
            wayland_layout.addWidget(wayland_info)
            
            # Check if wf-recorder is installed
            try:
                subprocess.check_output(["which", "wf-recorder"], stderr=subprocess.PIPE)
                wf_status = QLabel("✓ wf-recorder is installed")
                wf_status.setStyleSheet("color: green;")
            except:
                wf_status = QLabel("✗ wf-recorder is not installed")
                wf_status.setStyleSheet("color: red;")
                
                install_button = QPushButton("Install wf-recorder")
                install_button.clicked.connect(self.on_install_wfrecorder)
                wayland_layout.addWidget(install_button)
                
            wayland_layout.addWidget(wf_status)
            advanced_layout.addRow("Wayland Support:", wayland_frame)
        
        settings_layout.addWidget(advanced_group)
        
        # Apply button
        apply_layout = QHBoxLayout()
        apply_layout.addStretch()
        
        apply_button = QPushButton("Apply Settings")
        apply_button.clicked.connect(self.on_apply_settings)
        apply_layout.addWidget(apply_button)
        
        settings_layout.addLayout(apply_layout)
        settings_layout.addStretch()
        
        return settings_widget
    
    def create_about_tab(self):
        """Create the about tab"""
        about_widget = QWidget()
        about_layout = QVBoxLayout(about_widget)
        
        # Logo
        logo_layout = QHBoxLayout()
        logo_layout.addStretch()
        
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets/manjcast.png"
        )
        
        if os.path.exists(logo_path):
            logo_label = QLabel()
            logo_pixmap = QPixmap(logo_path)
            logo_label.setPixmap(logo_pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo_layout.addWidget(logo_label)
        
        logo_layout.addStretch()
        about_layout.addLayout(logo_layout)
        
        # App name and version
        name_label = QLabel("ManjCast")
        name_label.setAlignment(Qt.AlignCenter)
        name_font = QFont()
        name_font.setPointSize(18)
        name_font.setBold(True)
        name_label.setFont(name_font)
        about_layout.addWidget(name_label)
        
        version_label = QLabel("Version 1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(version_label)
        
        # Description
        description_label = QLabel(
            "ManjCast is a screen casting tool for Manjaro Linux "
            "that allows you to cast your screen to any Google Cast compatible device."
        )
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(description_label)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        about_layout.addWidget(line)
        
        # System info
        sys_info_label = QLabel("System Information:")
        sys_info_label.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(sys_info_label)
        
        # Desktop Environment
        de_label = QLabel(f"Desktop Environment: {self.cast_manager.screen_capture.desktop_environment.upper()}")
        de_label.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(de_label)
        
        # Session Type
        session_type = os.environ.get("XDG_SESSION_TYPE", "unknown").upper()
        session_label = QLabel(f"Session Type: {session_type}")
        session_label.setAlignment(Qt.AlignCenter)
        about_layout.addWidget(session_label)
        
        # Add note about Wayland if applicable
        if self.is_wayland:
            wayland_note = QLabel(
                "Note: You are running in a Wayland session. For optimal performance,\n"
                "consider logging in with an X11 session instead."
            )
            wayland_note.setStyleSheet("color: #FF6700;")
            wayland_note.setAlignment(Qt.AlignCenter)
            about_layout.addWidget(wayland_note)
        
        # Links
        links_layout = QHBoxLayout()
        links_layout.addStretch()
        
        github_button = QPushButton("GitHub")
        github_button.clicked.connect(lambda: QApplication.instance().openUrl("https://github.com/yourusername/manjcast"))
        links_layout.addWidget(github_button)
        
        issues_button = QPushButton("Report Issue")
        issues_button.clicked.connect(lambda: QApplication.instance().openUrl("https://github.com/yourusername/manjcast/issues"))
        links_layout.addWidget(issues_button)
        
        links_layout.addStretch()
        about_layout.addLayout(links_layout)
        
        about_layout.addStretch()
        
        return about_widget
    
    def update_device_list(self, devices):
        """Update the list of devices"""
        self.device_list.clear()
        
        for uuid, device in devices.items():
            item = QListWidgetItem(f"{device['name']} ({device['model_name']})")
            item.setData(Qt.UserRole, uuid)
            self.device_list.addItem(item)
    
    def update_window_list(self):
        """Update the list of windows"""
        self.window_combo.clear()
        
        # Get the list of windows
        windows = self.cast_manager.screen_capture.get_window_list()
        
        for window_id, window_title in windows.items():
            self.window_combo.addItem(window_title, window_id)
        
        # If we're on Wayland and didn't get any windows, add a "Full Desktop" option
        if self.is_wayland and self.window_combo.count() == 0:
            self.window_combo.addItem("Full Desktop", "desktop")
    
    def update_ui_state(self):
        """Update the UI based on the current state"""
        is_casting = self.cast_manager.is_casting
        has_device = self.cast_manager.current_device is not None
        
        # Buttons
        self.start_button.setEnabled(has_device and not is_casting)
        self.stop_button.setEnabled(is_casting)
        
        # Device list
        self.device_list.setEnabled(not is_casting)
        
        # Cast options
        self.screen_radio.setEnabled(not is_casting)
        self.window_radio.setEnabled(not is_casting)
        self.window_combo.setEnabled(not is_casting and self.window_radio.isChecked())
        self.audio_checkbox.setEnabled(not is_casting)
        
        # Status label
        if is_casting:
            device_name = "unknown device"
            if self.cast_manager.current_device:
                device_name = self.cast_manager.current_device.device.friendly_name
            self.status_label.setText(f"Casting to {device_name}")
        else:
            if has_device:
                self.status_label.setText("Ready to cast")
            else:
                self.status_label.setText("Select a device to cast to")
    
    def update_cast_status(self, status):
        """Update the UI based on cast status changes"""
        if status == "started":
            self.statusBar().showMessage("Casting started")
            self.status_label.setText("Casting")
            self.update_ui_state()
        elif status == "stopped":
            self.statusBar().showMessage("Casting stopped")
            self.status_label.setText("Not casting")
            self.update_ui_state()
        elif status == "error":
            self.statusBar().showMessage("Error during casting")
            self.status_label.setText("Error")
            self.update_ui_state()
            
            # Show error dialog
            QMessageBox.critical(
                self,
                "Casting Error",
                "An error occurred during casting. Please check the logs for details."
            )
        elif status == "disconnected":
            self.statusBar().showMessage("Disconnected from device")
            self.status_label.setText("Disconnected")
            self.update_ui_state()
    
    def show_wayland_warning(self):
        """Show a warning about Wayland limitations"""
        QMessageBox.warning(
            self, 
            "Wayland Session Detected",
            "You are running ManjCast in a Wayland session. Screen casting may have limited functionality.\n\n"
            "For best results:\n"
            "1. Install wf-recorder for better Wayland support\n"
            "2. Or log in using an X11 session instead\n\n"
            "You can continue using ManjCast, but some features may not work as expected."
        )
    
    def on_install_wfrecorder(self):
        """Handle clicking on install wf-recorder button"""
        reply = QMessageBox.question(
            self,
            "Install wf-recorder",
            "This will attempt to install wf-recorder using 'sudo pacman'.\n\n"
            "You may be prompted for your password. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Run the installation command
                import subprocess
                cmd = ["pkexec", "pacman", "-S", "wf-recorder"]
                subprocess.Popen(cmd)
                
                QMessageBox.information(
                    self,
                    "Installation Started",
                    "The installation of wf-recorder has been started.\n"
                    "Please restart ManjCast after installation completes."
                )
            except Exception as e:
                logger.error(f"Error installing wf-recorder: {e}")
                QMessageBox.critical(
                    self,
                    "Installation Error",
                    f"An error occurred while trying to install wf-recorder: {e}"
                )
    
    @pyqtSlot()
    def on_refresh_devices(self):
        """Handle refresh devices button"""
        self.statusBar().showMessage("Refreshing devices...")
        
        # Restart device discovery
        self.device_discovery.stop_discovery()
        self.device_discovery.start_discovery()
    
    @pyqtSlot(QListWidgetItem)
    def on_device_selected(self, item):
        """Handle device selection"""
        device_uuid = item.data(Qt.UserRole)
        
        # Try to select the device
        success = self.cast_manager.select_device(device_uuid)
        
        if success:
            self.statusBar().showMessage(f"Selected device: {item.text()}")
        else:
            self.statusBar().showMessage("Failed to connect to device")
            
        # Update UI state
        self.update_ui_state()
    
    @pyqtSlot()
    def on_cast_mode_changed(self):
        """Handle cast mode radio button changes"""
        # Update the window combo box enabled state
        self.window_combo.setEnabled(self.window_radio.isChecked())
        
        # If window mode is selected, update the window list
        if self.window_radio.isChecked():
            self.update_window_list()
    
    @pyqtSlot(int)
    def on_audio_option_changed(self, state):
        """Handle audio checkbox changes"""
        self.cast_manager.set_audio_enabled(state == Qt.Checked)
    
    @pyqtSlot()
    def on_start_casting(self):
        """Handle start casting button"""
        # Set cast mode
        if self.screen_radio.isChecked():
            self.cast_manager.set_cast_mode("screen")
        else:
            window_id = self.window_combo.currentData()
            if window_id:
                self.cast_manager.set_cast_mode("window", window_id)
            else:
                QMessageBox.warning(
                    self,
                    "No Window Selected",
                    "Please select a window to cast."
                )
                return
        
        # Set audio option
        self.cast_manager.set_audio_enabled(self.audio_checkbox.isChecked())
        
        # Start casting
        success = self.cast_manager.start_casting()
        
        if success:
            self.statusBar().showMessage("Casting started")
            
            # If minimize to tray is enabled, minimize the window
            if self.minimize_checkbox.isChecked():
                self.hide()
        else:
            self.statusBar().showMessage("Failed to start casting")
            
            QMessageBox.critical(
                self,
                "Casting Error",
                "Failed to start casting. Please check the logs for details."
            )
    
    @pyqtSlot()
    def on_stop_casting(self):
        """Handle stop casting button"""
        self.cast_manager.stop_casting()
        self.statusBar().showMessage("Casting stopped")
    
    @pyqtSlot(int)
    def on_minimize_changed(self, state):
        """Handle minimize to tray checkbox changes"""
        minimize_to_tray = state == Qt.Checked
        self.cast_manager.config['GENERAL']['minimize_to_tray'] = str(minimize_to_tray).lower()
    
    @pyqtSlot(int)
    def on_autostart_changed(self, state):
        """Handle start with system checkbox changes"""
        start_with_system = state == Qt.Checked
        self.cast_manager.config['GENERAL']['start_with_system'] = str(start_with_system).lower()
        
        # Create or remove the autostart entry based on the desktop environment
        desktop_env = self.cast_manager.screen_capture.desktop_environment
        
        try:
            if desktop_env == "gnome":
                from ui.gnome_integration import GnomeIntegration
                gnome = GnomeIntegration()
                gnome.setup_autostart(start_with_system)
            elif desktop_env == "kde":
                from ui.kde_integration import KdeIntegration
                kde = KdeIntegration()
                kde.setup_autostart(start_with_system)
            elif desktop_env == "xfce":
                from ui.xfce_integration import XfceIntegration
                xfce = XfceIntegration()
                xfce.setup_autostart(start_with_system)
            else:
                # Generic method - use desktop_integration.sh script
                import subprocess
                script_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "scripts/desktop_integration.sh"
                )
                if os.path.exists(script_path):
                    subprocess.run([script_path])
        except Exception as e:
            logger.error(f"Error setting up autostart: {e}")
    
    @pyqtSlot(str)
    def on_resolution_changed(self, text):
        """Handle resolution combo box changes"""
        # TODO: Handle custom resolution
        self.cast_manager.config['CASTING']['resolution'] = text
    
    @pyqtSlot(str)
    def on_framerate_changed(self, text):
        """Handle framerate combo box changes"""
        self.cast_manager.config['CASTING']['framerate'] = text
    
    @pyqtSlot(str)
    def on_timeout_changed(self, text):
        """Handle timeout combo box changes"""
        self.cast_manager.config['ADVANCED']['discovery_timeout'] = text
    
    @pyqtSlot()
    def on_apply_settings(self):
        """Handle apply settings button"""
        # Save config to file
        config_path = os.path.expanduser("~/.config/manjcast/config.ini")
        with open(config_path, 'w') as config_file:
            self.cast_manager.config.write(config_file)
        
        self.statusBar().showMessage("Settings saved")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # If minimizing to tray is enabled and casting is active, minimize instead of closing
        if self.minimize_checkbox.isChecked() and self.cast_manager.is_casting:
            event.ignore()
            self.hide()
            return
        
        # Stop casting if active
        if self.cast_manager.is_casting:
            reply = QMessageBox.question(
                self,
                "ManjCast",
                "Casting is still active. Are you sure you want to quit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.cast_manager.stop_casting()
                event.accept()
            else:
                event.ignore()
                return
        
        # Stop device discovery
        self.device_discovery.stop_discovery()
        
        # Save settings
        config_path = os.path.expanduser("~/.config/manjcast/config.ini")
        with open(config_path, 'w') as config_file:
            self.cast_manager.config.write(config_file)
        
        event.accept()
