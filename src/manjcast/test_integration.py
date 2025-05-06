#!/usr/bin/env python3
"""
Integration test script for ManjCast.
Demonstrates the complete workflow of device discovery, selection, and streaming.
"""

import logging
import sys
import time
from .core.cast_streamer import CastStreamer

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('test_integration')
    
    # Create streamer instance
    streamer = CastStreamer()
    
    try:
        print("\nמחפש מכשירי Cast זמינים...")
        devices = streamer.discover_devices()
        
        if not devices:
            print("\nלא נמצאו מכשירי Cast ברשת.")
            print("\nאנא בדוק:")
            print("1. שמכשירי ה-Cast שלך מופעלים")
            print("2. שאתה מחובר לאותה רשת WiFi כמו המכשירים")
            print("3. שהרשת מאפשרת גילוי מכשירים (mDNS/Zeroconf)")
            return
        
        # Show available devices
        print(f"\nנמצאו {len(devices)} מכשירי Cast:")
        for i, device in enumerate(devices, 1):
            print(f"{i}. {device['name']} ({device['ip_address']})")
        
        # Get user selection
        while True:
            try:
                choice = input("\nבחר מספר מכשיר (או 'q' ליציאה): ")
                if choice.lower() == 'q':
                    return
                
                idx = int(choice) - 1
                if 0 <= idx < len(devices):
                    selected_device = devices[idx]
                    break
                else:
                    print("בחירה לא תקינה. נסה שוב.")
            except ValueError:
                print("בחירה לא תקינה. הקש מספר או 'q' ליציאה.")
        
        # Select the device
        print(f"\nמתחבר למכשיר {selected_device['name']}...")
        if not streamer.select_device(selected_device):
            print("החיבור למכשיר נכשל.")
            return
        
        # Start streaming
        print("\nמתחיל שידור מסך...")
        streamer.start_streaming()
        
        print("\nשידור המסך פעיל.")
        print("לחץ Ctrl+C לעצירה")
        
        # Keep running until user interrupts
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nעוצר את השידור...")
        streamer.stop_streaming()
        print("השידור נעצר")
    except Exception as e:
        logger.error(f"שגיאה: {e}")
        if streamer.is_streaming:
            print("\nעוצר את השידור...")
            streamer.stop_streaming()
        sys.exit(1)

if __name__ == "__main__":
    main()