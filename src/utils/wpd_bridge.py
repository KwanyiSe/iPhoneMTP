#wpd_bridge.py
import os
import subprocess
from integration.ios_namespace import register_namespace_extension

class WPDBridge:
    def detect_devices(self):
        result = subprocess.run(["idevice_id", "-l"], capture_output=True, text=True)
        return result.stdout.splitlines()

    def get_device_name(self, udid):
        result = subprocess.run(
            ["ideviceinfo", "-u", udid, "-k", "DeviceName"],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() or "iPhone"

    def register_device(self, device_name, udid):
        display_name = (
            f"{device_name} iPhone"
            if not device_name.lower().endswith("iphone")
            else device_name
        )
        print(f"Registering {display_name} ({udid}) under This PC...")
        register_namespace_extension(display_name)

        base_path = os.path.join(r"C:\ios_connect", udid)
        os.makedirs(base_path, exist_ok=True)
        self.populate_device_tree(base_path)
        return base_path

    def populate_device_tree(self, base_path):
        folders = [
            "DCIM",
            os.path.join("AppData", "WhatsApp"),
            os.path.join("AppData", "Telegram"),
            os.path.join("AppData", "Others"),
            "Backups",
            "Diagnostics"
        ]
        for folder in folders:
            path = os.path.join(base_path, folder)
            os.makedirs(path, exist_ok=True)
            if "Diagnostics" in folder:
                subprocess.run(["attrib", "+h", path], shell=True)
                print(f"Created hidden folder: {path}")
            else:
                print(f"Created folder: {path}")