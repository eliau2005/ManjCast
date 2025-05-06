#!/usr/bin/env python3
"""
Main entry point for ManjCast application.
"""

import sys
import logging
from PySide6.QtWidgets import QApplication
from .ui.main_window import MainWindow

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()