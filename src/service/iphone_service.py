#background services.py
import time
import subprocess
import ctypes
import os
from core.device_manager import DeviceManager
from core.sync_manager import SyncManager
from integration.wpd_bridge import WPDBridge
from integration.ios_namespace import (
    IOSConnectNamespace,
    remove_from_explorer_namespace
)

class BackgroundService:
    def __init__(self):
        self.manager = DeviceManager()
        self.wpd = WPDBridge()
        # Track registered devices by UDID
        self.registered_devices = set()

    def run(self):
        print("Background service started...")
        while True:
            devices = set(self.manager.detect_devices())

            # Handle newly connected devices
            new_devices = devices - self.registered_devices
            for udid in new_devices:
                device_name = self.wpd.get_device_name(udid)
                display_name = (
                    f"{device_name} iPhone"
                    if not device_name.lower().endswith("iphone")
                    else device_name
                )
                print(f"New device connected: {display_name} ({udid})")

                # Register namespace node for this device
                self.wpd.register_device(display_name, udid)
                self._refresh_explorer()
                self.registered_devices.add(udid)

                # Perform sync operations (placeholders)
                mount_path = os.path.join(r"C:\ios_connect", udid)
                sync = SyncManager(mount_path, udid)
                sync.ensure_phone_folders()
                sync.sync_pc_to_phone()
                sync.sync_phone_to_pc()
                sync.write_diagnostics_log(
                    f"Synced {display_name} ({udid}) successfully"
                )

                # Open Explorer only once when device first connects
                subprocess.run(["explorer", mount_path])

            # Handle disconnected devices
            removed_devices = self.registered_devices - devices
            for udid in removed_devices:
                print(f"Device disconnected: {udid}")
                remove_from_explorer_namespace(IOSConnectNamespace._reg_clsid_)
                self._refresh_explorer()
                self.registered_devices.remove(udid)

            # Sleep before checking again
            time.sleep(5)

    def _refresh_explorer(self):
        """
        Broadcast a shell change notification so Explorer refreshes immediately.
        Ensures nodes appear/disappear without manual refresh.
        """
        ctypes.windll.shell32.SHChangeNotify(0x8000000, 0x1000, None, None)