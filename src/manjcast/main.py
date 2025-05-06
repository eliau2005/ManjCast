#!/usr/bin/env python3
"""
Main entry point for ManjCast application.
"""

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from qt_material import apply_stylesheet
from .ui.main_window import MainWindow

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("ManjCast")
    app.setApplicationVersion("1.0.0")
    
    # Apply Material Design theme
    apply_stylesheet(app, theme='light_blue.xml')
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())