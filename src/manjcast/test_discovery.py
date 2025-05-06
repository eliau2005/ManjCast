#!/usr/bin/env python3
"""
Test script for demonstrating the Cast device discovery functionality.
"""

import logging
import sys
from .core.device_discovery import CastDeviceScanner, DeviceDiscoveryError

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger('test_discovery')
    
    # Create scanner instance
    scanner = CastDeviceScanner()
    
    try:
        print("\nסורק מכשירי Cast ברשת המקומית...")
        devices = scanner.start_discovery()
        
        if not devices:
            print("\nלא נמצאו מכשירי Cast ברשת.")
            print("\nאנא בדוק:")
            print("1. שמכשירי ה-Cast שלך מופעלים")
            print("2. שאתה מחובר לאותה רשת WiFi כמו המכשירים")
            print("3. שהרשת מאפשרת גילוי מכשירים (mDNS/Zeroconf)")
            print("4. שאכן יש לך מכשירי Cast ברשת")
            print("\nניתן לבצע סריקה נוספת על ידי הרצה חוזרת של הסקריפט.")
            return
        
        print(f"\nנמצאו {len(devices)} מכשירי Cast:")
        print("-" * 50)
        
        for device in devices:
            print(f"שם המכשיר: {device['name']}")
            print(f"כתובת IP: {device['ip_address']}")
            print(f"דגם: {device['model_name']}")
            print(f"סוג: {device['cast_type']}")
            print("-" * 50)
            
    except DeviceDiscoveryError as e:
        print(f"\nשגיאה בגילוי מכשירים: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nסריקת המכשירים בוטלה על ידי המשתמש.")
        sys.exit(0)
    except Exception as e:
        print(f"\nשגיאה בלתי צפויה: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()