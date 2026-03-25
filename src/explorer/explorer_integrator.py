#explorer_intergrator.py
import os
import win32com.client

class ExplorerIntegrator:
    def __init__(self, mount_root="C:\\ios_mount"):
        self.mount_root = mount_root
        os.makedirs(mount_root, exist_ok=True)

    def create_mount_point(self, udid):
        """Create a folder for the device and add Explorer shortcut"""
        mount_path = os.path.join(self.mount_root, udid)
        os.makedirs(mount_path, exist_ok=True)

        # Create Explorer shortcut on Desktop
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        shortcut_path = os.path.join(desktop, f"iPhone_{udid}.lnk")

        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = mount_path
        shortcut.WorkingDirectory = mount_path
        shortcut.IconLocation = "shell32.dll, 3"  # generic folder icon
        shortcut.save()

        return mount_path