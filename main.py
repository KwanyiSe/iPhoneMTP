#main.py
import sys
import os

from services.background_service import BackgroundService
from integration.ios_namespace import register_namespace_extension
from integration.wpd_bridge import WPDBridge

def main():
    print("=== iOS Connect starting ===")

    # Step 1: Detect devices and register Explorer namespace extension
    wpd = WPDBridge()
    devices = wpd.detect_devices()
    if devices:
        udid = devices[0]  # take the first connected device
        device_name = wpd.get_device_name(udid)
        print(f"Registering Explorer namespace extension for {device_name}...")
        register_namespace_extension(device_name)
    else:
        print("No devices detected at startup, namespace not registered yet.")

    # Step 2: Start background service (backend + integration)
    service = BackgroundService()
    service.run()

if __name__ == "__main__":
    main()