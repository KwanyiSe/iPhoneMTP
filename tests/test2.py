import ctypes
import subprocess
import os

class LibIMobileDeviceWrapper:
    def __init__(self):
        self.lib = ctypes.CDLL(r"C:\libimobiledevice\bin\libimobiledevice-1.0.dll")

        class AFCClient(ctypes.Structure):
            pass
        self.AFCClient_p = ctypes.POINTER(AFCClient)

        class HouseArrestClient(ctypes.Structure):
            pass
        self.HAClient_p = ctypes.POINTER(HouseArrestClient)

        # idevice + lockdown
        self.lib.idevice_new.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_char_p]
        self.lib.idevice_new.restype = ctypes.c_int

        self.lib.lockdownd_client_new_with_handshake.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p), ctypes.c_char_p
        ]
        self.lib.lockdownd_client_new_with_handshake.restype = ctypes.c_int

        # House Arrest
        self.lib.house_arrest_client_start_service.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(self.HAClient_p), ctypes.c_char_p
        ]
        self.lib.house_arrest_client_start_service.restype = ctypes.c_int

        self.lib.house_arrest_send_command.argtypes = [self.HAClient_p, ctypes.c_char_p]
        self.lib.house_arrest_send_command.restype = ctypes.c_int

        self.lib.afc_client_new.argtypes = [ctypes.c_void_p, ctypes.POINTER(self.AFCClient_p)]
        self.lib.afc_client_new.restype = ctypes.c_int

        # AFC functions
        self.lib.afc_read_directory.argtypes = [
            self.AFCClient_p, ctypes.c_char_p, ctypes.POINTER(ctypes.POINTER(ctypes.c_char_p))
        ]
        self.lib.afc_read_directory.restype = ctypes.c_int

        self.lib.afc_file_open.argtypes = [self.AFCClient_p, ctypes.c_char_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64)]
        self.lib.afc_file_open.restype = ctypes.c_int

        self.lib.afc_file_write.argtypes = [self.AFCClient_p, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
        self.lib.afc_file_write.restype = ctypes.c_int

        self.lib.afc_file_close.argtypes = [self.AFCClient_p, ctypes.c_uint64]
        self.lib.afc_file_close.restype = ctypes.c_int

        self.afc_client = None

    @staticmethod
    def list_devices():
        result = subprocess.run([r"C:\libimobiledevice\bin\idevice_id.exe", "-l"],
                                capture_output=True, text=True)
        return result.stdout.strip().split("\n") if result.stdout else []

    def connect_house_arrest(self, udid: str, bundle_id: str):
        device = ctypes.c_void_p()
        if self.lib.idevice_new(ctypes.byref(device), udid.encode("utf-8")) != 0:
            raise RuntimeError("Failed to connect to device")

        lockdown = ctypes.c_void_p()
        if self.lib.lockdownd_client_new_with_handshake(device, ctypes.byref(lockdown), None) != 0:
            raise RuntimeError("Failed to start lockdownd")

        ha_client = self.HAClient_p()
        if self.lib.house_arrest_client_start_service(device, ctypes.byref(ha_client), None) != 0:
            raise RuntimeError("Failed to start House Arrest service")

        # Tell House Arrest we want the Documents folder
        if self.lib.house_arrest_send_command(ha_client, b"VendDocuments") != 0:
            raise RuntimeError("House Arrest command failed")

        # Attach AFC client to House Arrest
        afc_client = self.AFCClient_p()
        if self.lib.afc_client_new(device, ctypes.byref(afc_client)) != 0:
            raise RuntimeError("Failed to attach AFC client to House Arrest")

        self.afc_client = afc_client
        return afc_client

    def list_folder(self, afc_client, path: str):
        dirlist = ctypes.POINTER(ctypes.c_char_p)()
        res = self.lib.afc_read_directory(afc_client, path.encode("utf-8"), ctypes.byref(dirlist))
        if res != 0:
            return []
        entries = []
        i = 0
        while dirlist[i]:
            entries.append(dirlist[i].decode("utf-8"))
            i += 1
        return entries

    def write_file(self, afc_client, path: str, content: bytes):
        handle = ctypes.c_uint64()
        if self.lib.afc_file_open(afc_client, path.encode("utf-8"), 2, ctypes.byref(handle)) != 0:
            raise RuntimeError("Failed to open file for writing")

        written = ctypes.c_uint32()
        res = self.lib.afc_file_write(afc_client, handle, content, len(content), ctypes.byref(written))
        if res != 0 or written.value != len(content):
            raise RuntimeError("Failed to write file")

        self.lib.afc_file_close(afc_client, handle)

    def sync_file(self, afc_client, local_path: str, device_folder: str):
        filename = os.path.basename(local_path)
        with open(local_path, "rb") as f:
            content = f.read()
        self.write_file(afc_client, f"{device_folder}/{filename}", content)