#ios_namespace file
import os
import pythoncom
import win32com.server.register
import winreg

from core.device_manager import DeviceManager
from core.sync_manager import SyncManager

IOS_CONNECT_ROOT = r"C:\ios_connect"

class IOSConnectNamespace:
    _reg_clsid_ = "{7204b4ae-e35b-4b93-a9b3-6bbd5ebdb69f}"
    _reg_desc_ = ""   # dynamically set
    _reg_progid_ = "IOSConnect.Device"
    _reg_clsctx_ = pythoncom.CLSCTX_INPROC_SERVER
    _public_methods_ = ["EnumObjects", "GetDisplayNameOf"]

    def __init__(self):
        self.device_manager = DeviceManager()

    def EnumObjects(self, hwnd, grfFlags):
        devices = self.device_manager.detect_devices()
        if not devices:
            return FolderEnumerator([])
        children = []
        for udid in devices:
            mount_path = os.path.join(IOS_CONNECT_ROOT, udid)
            sync = SyncManager(mount_path, udid)
            sync.ensure_phone_folders()
            children.append(udid)
        return FolderEnumerator(children)

    def GetDisplayNameOf(self, pidl, uFlags):
        udid = pidl if isinstance(pidl, str) else None
        if not udid:
            return "Unknown iPhone"
        info = self.device_manager.get_info(udid)
        if info:
            for line in info.splitlines():
                if line.startswith("DeviceName:") or line.startswith("Device Name:"):
                    return line.split(":", 1)[1].strip()
        return f"iPhone ({udid})"

class FolderEnumerator:
    _public_methods_ = ["Next", "Skip", "Reset", "Clone"]

    def __init__(self, folders):
        self._folders = folders
        self._index = 0

    def Next(self, celt):
        if self._index < len(self._folders):
            item = self._folders[self._index]
            self._index += 1
            return [item], 1
        return [], 0

    def Skip(self, celt):
        self._index = min(self._index + celt, len(self._folders))

    def Reset(self):
        self._index = 0

    def Clone(self):
        return FolderEnumerator(self._folders)

def add_to_explorer_namespace(clsid, description):
    """
    Add CLSID entry under both MyComputer and Desktop namespaces,
    and pin to navigation pane.
    """
    paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\MyComputer\NameSpace",
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Desktop\NameSpace"
    ]
    for key_path in paths:
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as ns_key:
            with winreg.CreateKey(ns_key, clsid) as subkey:
                winreg.SetValue(subkey, "", winreg.REG_SZ, description)

    # Pin to navigation pane
    nav_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Desktop\NameSpace\\" + clsid
    with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, nav_path) as nav_key:
        winreg.SetValueEx(nav_key, "System.IsPinnedToNamespaceTree", 0, winreg.REG_DWORD, 1)

    print(f"Added CLSID {clsid} to Explorer Namespace with description '{description}'")

def remove_from_explorer_namespace(clsid):
    paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\MyComputer\NameSpace",
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Desktop\NameSpace"
    ]
    for key_path in paths:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_WRITE) as ns_key:
                winreg.DeleteKey(ns_key, clsid)
                print(f"Removed CLSID {clsid} from {key_path}")
        except FileNotFoundError:
            pass

def register_namespace_extension(device_name):
    """
    Register the namespace extension dynamically with the actual device name.
    Assign a custom icon shipped with the installer.
    """
    win32com.server.register.UseCommandLine(IOSConnectNamespace)
    key_path = r"CLSID\\" + IOSConnectNamespace._reg_clsid_

    with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as clsid_key:
        winreg.SetValue(clsid_key, "", winreg.REG_SZ, device_name)

        # Custom icon shipped with installer
        icon_path = r"C:\ios_connect\iphone.ico"
        with winreg.CreateKey(clsid_key, "DefaultIcon") as icon_key:
            winreg.SetValue(icon_key, "", winreg.REG_SZ, icon_path)

        # ShellFolder entry so Explorer knows it’s a folder
        with winreg.CreateKey(clsid_key, "ShellFolder") as shell_key:
            # 0x28 marks it as a filesystem folder that can be pinned
            winreg.SetValueEx(shell_key, "Attributes", 0, winreg.REG_DWORD, 0x28)
            winreg.SetValue(shell_key, "FolderPath", winreg.REG_SZ, IOS_CONNECT_ROOT)

    add_to_explorer_namespace(IOSConnectNamespace._reg_clsid_, device_name)