#syn_manager.py
import os
import subprocess

class SyncManager:
    def __init__(self, mount_path_pc, udid):
        self.mount_path_pc = mount_path_pc
        self.udid = udid

    def ensure_phone_folders(self):
        """
        Ensure the PC-side folder tree exists.
        Diagnostics is hidden.
        """
        phone_folders = [
            "DCIM",
            os.path.join("AppData", "WhatsApp"),
            os.path.join("AppData", "Telegram"),
            os.path.join("AppData", "Others"),
            "Backups",
            "Diagnostics"  # hidden/internal
        ]
        for folder in phone_folders:
            path = os.path.join(self.mount_path_pc, folder)
            os.makedirs(path, exist_ok=True)
            if "Diagnostics" in folder:
                subprocess.run(["attrib", "+h", path], shell=True)
                print(f"Created hidden folder: {path}")
            else:
                print(f"Created folder: {path}")

    def sync_pc_to_phone(self):
        """
        PC → Phone sync skipped.
        Placeholder only.
        """
        print("PC → Phone sync skipped (feature placeholder)")

    def sync_phone_to_pc(self):
        """
        Phone → PC sync skipped.
        DCIM, AppData, Backups are placeholders.
        """
        print("Phone → PC sync skipped (feature placeholders)")

    def write_diagnostics_log(self, message):
        """
        Save a log entry into Diagnostics (hidden) on PC.
        """
        diag_path = os.path.join(self.mount_path_pc, "Diagnostics", "sync.log")
        os.makedirs(os.path.dirname(diag_path), exist_ok=True)
        with open(diag_path, "a") as f:
            f.write(message + "\n")
        subprocess.run(["attrib", "+h", os.path.dirname(diag_path)], shell=True)
        print("Wrote log entry to hidden Diagnostics folder")