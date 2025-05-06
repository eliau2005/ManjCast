"""
Main window for ManjCast application.
Provides GUI interface for Cast device discovery and screen streaming.
"""

import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QComboBox, QPushButton, QLabel, QStatusBar,
    QMessageBox, QApplication, QRadioButton,
    QButtonGroup, QGroupBox, QFrame
)
from PySide6.QtCore import Qt, QTimer, Slot, QSize
from PySide6.QtGui import QIcon, QColor, QFont
from qt_material import apply_stylesheet, list_themes

# Add parent directory to path so we can import core modules
sys.path.append(str(Path(__file__).parent.parent))
from ..core.cast_streamer import CastStreamer
from .window_selector import WindowSelector

# Configure logging
logger = logging.getLogger(__name__)

class MaterialCard(QFrame):
    """A Material Design card widget."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty('class', 'material-card')
        self.setObjectName('material-card')

class MainWindow(QMainWindow):
    """Main window of the ManjCast application."""
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        # Get web root path
        web_root = str(Path(__file__).parent / 'web')
        
        # Initialize core components with web support
        self._streamer = CastStreamer(web_root=web_root)
        self._devices: List[Dict] = []
        self._selected_window_id: Optional[str] = None
        
        # Apply Google Cast themed style
        apply_stylesheet(self, theme='light_blue.xml', extra={
            'font_family': 'Roboto',
            'font_size': '14px',
            'primary': '#1A73E8',  # Google Blue
            'secondary': '#4285F4',
            'success': '#34A853',  # Google Green
            'warning': '#FBBC05',  # Google Yellow
            'danger': '#EA4335',   # Google Red
            'density': 0,
            'button_radius': '4px',
            'card_radius': '8px',
        })

        # Set up window properties
        self.setWindowTitle("ManjCast")
        self.setMinimumSize(800, 600)
        self.setWindowIcon(QIcon.fromTheme("cast", QIcon(":/icons/cast.png")))
        
        # Create central widget with padding
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # Create device selection card
        device_card = MaterialCard()
        device_card.setStyleSheet("""
            #material-card {
                background: white;
                border-radius: 8px;
                padding: 16px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
        """)
        device_layout = QVBoxLayout(device_card)
        
        device_header = QLabel("התקני Google Cast")
        device_header.setFont(QFont("Roboto", 18, QFont.Weight.Medium))
        device_header.setStyleSheet("color: #202124;")  # Google's text color
        device_layout.addWidget(device_header)
        
        device_selector = QHBoxLayout()
        self.device_combo = QComboBox()
        self.device_combo.setPlaceholderText("חפש התקני Cast זמינים")
        self.device_combo.setMinimumHeight(48)
        self.device_combo.setFont(QFont("Roboto", 12))
        self.device_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #DADCE0;
                border-radius: 4px;
                padding: 8px 16px;
                background: white;
            }
            QComboBox:hover {
                border-color: #1A73E8;
            }
        """)
        
        self.refresh_button = QPushButton()
        self.refresh_button.setIcon(QIcon.fromTheme("view-refresh"))
        self.refresh_button.setIconSize(QSize(24, 24))
        self.refresh_button.setToolTip("רענן רשימת התקנים")
        self.refresh_button.setFixedSize(48, 48)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background: #F8F9FA;
                border: 1px solid #DADCE0;
                border-radius: 24px;
            }
            QPushButton:hover {
                background: #F1F3F4;
            }
        """)
        self.refresh_button.clicked.connect(self._refresh_devices)
        
        device_selector.addWidget(self.device_combo, 1)
        device_selector.addWidget(self.refresh_button)
        device_layout.addLayout(device_selector)
        
        main_layout.addWidget(device_card)
        
        # Create capture options card
        capture_card = MaterialCard()
        capture_card.setStyleSheet("""
            #material-card {
                background: white;
                border-radius: 8px;
                padding: 16px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
        """)
        capture_layout = QVBoxLayout(capture_card)
        
        capture_header = QLabel("אפשרויות שידור")
        capture_header.setProperty('class', 'h2')
        capture_layout.addWidget(capture_header)
        
        self.capture_full = QRadioButton("שדר מסך מלא")
        self.capture_window = QRadioButton("שדר חלון נבחר")
        self.select_window_button = QPushButton("בחר חלון...")
        self.select_window_button.setEnabled(False)
        self.select_window_button.setMinimumHeight(40)
        self.select_window_button.clicked.connect(self._select_window)
        
        self.capture_full.setChecked(True)
        self.capture_full.toggled.connect(self._capture_mode_changed)
        
        capture_layout.addWidget(self.capture_full)
        capture_layout.addWidget(self.capture_window)
        capture_layout.addWidget(self.select_window_button)
        
        main_layout.addWidget(capture_card)
        
        # Create streaming controls card
        controls_card = MaterialCard()
        controls_card.setStyleSheet("""
            #material-card {
                background: white;
                border-radius: 8px;
                padding: 16px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
        """)
        controls_layout = QVBoxLayout(controls_card)
        
        controls_header = QLabel("בקרת שידור")
        controls_header.setProperty('class', 'h2')
        controls_layout.addWidget(controls_header)
        
        self.stream_button = QPushButton("התחל שידור")
        self.stream_button.setMinimumHeight(48)
        self.stream_button.setProperty('class', 'primary')
        self.stream_button.clicked.connect(self._toggle_streaming)
        self.stream_button.setEnabled(False)
        self.stream_button.setStyleSheet("""
            QPushButton {
                background: #1A73E8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #1557B0;
            }
            QPushButton:disabled {
                background: #DFE1E5;
                color: #5F6368;
            }
        """)
        controls_layout.addWidget(self.stream_button)
        
        main_layout.addWidget(controls_card)
        
        # Add stretcher to push everything up
        main_layout.addStretch()
        
        # Create status bar with improved appearance
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background: #F8F9FA;
                border-top: 1px solid #DADCE0;
                padding: 8px 16px;
                font-size: 13px;
                color: #5F6368;
            }
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("מוכן")
        
        # Connect signals
        self.device_combo.currentIndexChanged.connect(self._device_selected)
        
        # Set up auto-refresh timer
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._refresh_devices)
        self._refresh_timer.start(30000)  # Refresh every 30 seconds
        
        # Initial device scan
        self._refresh_devices()
    
    @Slot()
    def _refresh_devices(self):
        """Refresh the list of available Cast devices."""
        try:
            self.status_bar.showMessage("מחפש התקני Cast...")
            self.refresh_button.setEnabled(False)
            
            # Clear current list
            self.device_combo.clear()
            self._devices.clear()
            
            # Get new device list
            devices = self._streamer.discover_devices()
            if not devices:
                self.status_bar.showMessage("לא נמצאו התקני Cast")
                return
            
            # Store devices and update combo box
            self._devices = devices
            for device in devices:
                self.device_combo.addItem(
                    f"{device['name']} ({device['ip_address']})", 
                    userData=device
                )
            
            self.status_bar.showMessage(f"נמצאו {len(devices)} התקני Cast")
            
        except Exception as e:
            logger.error(f"Error refreshing devices: {e}")
            self.status_bar.showMessage("שגיאה בחיפוש התקנים")
            QMessageBox.critical(
                self,
                "שגיאה",
                f"אירעה שגיאה בעת חיפוש התקנים:\n{str(e)}"
            )
        finally:
            self.refresh_button.setEnabled(True)
    
    @Slot(int)
    def _device_selected(self, index: int):
        """Handle device selection from combo box."""
        self.stream_button.setEnabled(index >= 0)
    
    @Slot(bool)
    def _capture_mode_changed(self, checked: bool):
        """Handle capture mode radio button changes."""
        self.select_window_button.setEnabled(self.capture_window.isChecked())
        if self.capture_full.isChecked():
            self._selected_window_id = None
    
    @Slot()
    def _select_window(self):
        """Show window selection dialog."""
        dialog = WindowSelector(self)
        if dialog.exec() == WindowSelector.Accepted:
            self._selected_window_id = dialog.get_selected_window()
    
    @Slot()
    def _toggle_streaming(self):
        """Toggle streaming start/stop."""
        if not self._streamer.is_streaming:
            self._start_streaming()
        else:
            self._stop_streaming()
    
    def _start_streaming(self):
        """Start streaming to selected device."""
        try:
            # Get selected device
            index = self.device_combo.currentIndex()
            if index < 0:
                return
            
            device = self._devices[index]
            self.status_bar.showMessage(f"מתחבר להתקן {device['name']}...")
            
            # Connect to device
            if not self._streamer.select_device(device):
                raise RuntimeError(f"לא ניתן להתחבר להתקן {device['name']}")
            
            # Verify window selection if needed
            if self.capture_window.isChecked() and not self._selected_window_id:
                raise RuntimeError("נא לבחור חלון לשידור")
            
            # Update streamer settings based on capture mode
            capture_settings = {
                'capture_type': 'fullscreen' if self.capture_full.isChecked() else 'window',
                'window_id': self._selected_window_id,
                'receiver_id': 'C0868879'  # Use Google's sample receiver app
            }
            self._streamer.settings = capture_settings
            
            # Start streaming
            self._streamer.start_streaming()
            
            # Update UI
            self.stream_button.setText("עצור שידור")
            self.device_combo.setEnabled(False)
            self.refresh_button.setEnabled(False)
            self.capture_full.setEnabled(False)
            self.capture_window.setEnabled(False)
            self.select_window_button.setEnabled(False)
            self.status_bar.showMessage(f"משדר למכשיר {device['name']}")
            
        except Exception as e:
            logger.error(f"Error starting stream: {e}")
            self.status_bar.showMessage("שגיאה בהתחלת השידור")
            QMessageBox.critical(
                self,
                "שגיאה",
                f"אירעה שגיאה בהתחלת השידור:\n{str(e)}"
            )
    
    def _stop_streaming(self):
        """Stop current streaming session."""
        try:
            self._streamer.stop_streaming()
            
            # Update UI
            self.stream_button.setText("התחל שידור")
            self.device_combo.setEnabled(True)
            self.refresh_button.setEnabled(True)
            self.capture_full.setEnabled(True)
            self.capture_window.setEnabled(True)
            self.select_window_button.setEnabled(self.capture_window.isChecked())
            self.status_bar.showMessage("השידור נעצר")
            
        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
            self.status_bar.showMessage("שגיאה בעצירת השידור")
            QMessageBox.critical(
                self,
                "שגיאה",
                f"אירעה שגיאה בעצירת השידור:\n{str(e)}"
            )
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self._streamer.is_streaming:
            self._stop_streaming()
        event.accept()