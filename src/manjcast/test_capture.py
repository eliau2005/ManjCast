#!/usr/bin/env python3
"""
Test script for demonstrating the screen capture functionality.
"""

import logging
import sys
import time
import os
from .core.screen_capture import ScreenCaptureManager, DisplayServer

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('test_capture')
    
    try:
        # Create capture manager
        capture = ScreenCaptureManager()
        
        # Show current settings
        print("\nהגדרות לכידת מסך נוכחיות:")
        print(f"שרת תצוגה: {capture._display_server.value}")
        print(f"הגדרות: {capture.settings}")
        
        # Create a test output pipe (you can modify this path)
        output_pipe = "/tmp/manjcast_test.raw"
        
        print("\nמתחיל לכידת מסך...")
        print("לחץ Ctrl+C כדי לעצור")
        
        # Start capture
        process = capture.start_capture(output_pipe)
        
        # Keep running until user interrupts
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nעוצר את לכידת המסך...")
        if 'process' in locals():
            capture.stop_capture(process)
        print("הלכידה נעצרה")
    except Exception as e:
        logger.error(f"שגיאה: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()