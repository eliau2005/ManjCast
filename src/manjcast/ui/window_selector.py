"""
Window selector dialog for ManjCast.
Allows users to select a specific window for streaming.
"""

import logging
import subprocess
from typing import Optional, Tuple
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QPushButton,
    QHBoxLayout, QListWidgetItem
)
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)

class WindowSelector(QDialog):
    """Dialog for selecting a window to stream."""
    
    def __init__(self, parent=None):
        """Initialize the window selector dialog."""
        super().__init__(parent)
        
        self.setWindowTitle("בחר חלון לשידור")
        self.setModal(True)
        self.resize(400, 300)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create window list
        self.window_list = QListWidget()
        self.window_list.setAlternatingRowColors(True)
        layout.addWidget(self.window_list)
        
        # Create buttons
        button_layout = QHBoxLayout()
        self.refresh_button = QPushButton("רענן")
        self.refresh_button.clicked.connect(self._refresh_windows)
        self.select_button = QPushButton("בחר")
        self.select_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("ביטול")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Initial window list population
        self._refresh_windows()
    
    def _refresh_windows(self):
        """Refresh the list of available windows."""
        self.window_list.clear()
        
        try:
            # Get window list using xwininfo or similar
            windows = self._get_window_list()
            
            for window_id, title in windows:
                item = QListWidgetItem(f"{title} ({window_id})")
                item.setData(Qt.UserRole, window_id)
                self.window_list.addItem(item)
                
        except Exception as e:
            logger.error(f"Failed to get window list: {e}")
    
    def _get_window_list(self) -> list[Tuple[str, str]]:
        """
        Get list of visible windows.
        
        Returns:
            List of tuples (window_id, window_title)
        """
        windows = []
        try:
            # Use wmctrl to get window list
            output = subprocess.check_output(['wmctrl', '-l'], text=True)
            
            for line in output.splitlines():
                parts = line.split(None, 3)
                if len(parts) >= 4:
                    window_id, workspace, host, title = parts
                    # Filter out desktop and panels
                    if not title.lower() in ['desktop', 'panel']:
                        windows.append((window_id, title))
                        
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to get window list: {e}")
            
        return windows
    
    def get_selected_window(self) -> Optional[str]:
        """
        Get the ID of the selected window.
        
        Returns:
            str: Window ID or None if no selection
        """
        item = self.window_list.currentItem()
        if item:
            return item.data(Qt.UserRole)
        return None