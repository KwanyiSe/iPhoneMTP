import ctypes
import subprocess

class LibIMobileDeviceWrapper:
    def __init__(self):
        self.lib = ctypes.CDLL(r"C:\libimobiledevice\bin\libimobiledevice-1.0.dll")

        class AFCClient(ctypes.Structure):
            pass
        self.AFCClient_p = ctypes.POINTER(AFCClient)

        class HouseArrestClient(ctypes.Structure):
            pass
        self.HouseArrestClient_p = ctypes.POINTER(HouseArrestClient)

        # Device + Lockdown
        self.lib.idevice_new.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_char_p]
        self.lib.idevice_new.restype = ctypes.c_int

        self.lib.lockdownd_client_new_with_handshake.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p), ctypes.c_char_p
        ]
        self.lib.lockdownd_client_new_with_handshake.restype = ctypes.c_int

        # AFC
        self.lib.afc_client_start_service.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(self.AFCClient_p), ctypes.c_char_p
        ]
        self.lib.afc_client_start_service.restype = ctypes.c_int

        self.lib.afc_read_directory.argtypes = [
            self.AFCClient_p, ctypes.c_char_p, ctypes.POINTER(ctypes.POINTER(ctypes.c_char_p))
        ]
        self.lib.afc_read_directory.restype = ctypes.c_int

        # File operations
        self.lib.afc_file_open.argtypes = [self.AFCClient_p, ctypes.c_char_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64)]
        self.lib.afc_file_open.restype = ctypes.c_int

        self.lib.afc_file_read.argtypes = [self.AFCClient_p, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
        self.lib.afc_file_read.restype = ctypes.c_int

        self.lib.afc_file_write.argtypes = [self.AFCClient_p, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
        self.lib.afc_file_write.restype = ctypes.c_int

        self.lib.afc_file_close.argtypes = [self.AFCClient_p, ctypes.c_uint64]
        self.lib.afc_file_close.restype = ctypes.c_int

        self.lib.afc_make_directory.argtypes = [self.AFCClient_p, ctypes.c_char_p]
        self.lib.afc_make_directory.restype = ctypes.c_int

        self.lib.afc_remove_path.argtypes = [self.AFCClient_p, ctypes.c_char_p]
        self.lib.afc_remove_path.restype = ctypes.c_int

        # House Arrest
        self.lib.house_arrest_client_start_service.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(self.HouseArrestClient_p), ctypes.c_char_p
        ]
        self.lib.house_arrest_client_start_service.restype = ctypes.c_int

        self.lib.house_arrest_send_command.argtypes = [self.HouseArrestClient_p, ctypes.c_char_p]
        self.lib.house_arrest_send_command.restype = ctypes.c_int

        self.lib.house_arrest_get_result.argtypes = [self.HouseArrestClient_p]
        self.lib.house_arrest_get_result.restype = ctypes.c_int

        self.lib.afc_client_new_from_house_arrest_client.argtypes = [
            self.HouseArrestClient_p, ctypes.POINTER(self.AFCClient_p)
        ]
        self.lib.afc_client_new_from_house_arrest_client.restype = ctypes.c_int

        self.afc_client = None

    @staticmethod
    def list_devices():
        result = subprocess.run([r"C:\libimobiledevice\bin\idevice_id.exe", "-l"],
                                capture_output=True, text=True)
        return result.stdout.strip().split("\n") if result.stdout else []

    def connect_afc(self, udid: str):
        device = ctypes.c_void_p()
        if self.lib.idevice_new(ctypes.byref(device), udid.encode("utf-8")) != 0:
            raise RuntimeError("Failed to connect to device")

        lockdown = ctypes.c_void_p()
        if self.lib.lockdownd_client_new_with_handshake(device, ctypes.byref(lockdown), None) != 0:
            raise RuntimeError("Failed to start lockdownd")

        afc_client = self.AFCClient_p()
        if self.lib.afc_client_start_service(device, ctypes.byref(afc_client), None) != 0:
            raise RuntimeError("Failed to start AFC client service")

        self.afc_client = afc_client

    def list_afc_root(self):
        return self.list_folder(self.afc_client, "")

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

    def connect_house_arrest(self, udid: str, app_id: str):
        device = ctypes.c_void_p()
        if self.lib.idevice_new(ctypes.byref(device), udid.encode("utf-8")) != 0:
            return None

        ha_client = self.HouseArrestClient_p()
        res = self.lib.house_arrest_client_start_service(device, ctypes.byref(ha_client), app_id.encode("utf-8"))
        if res != 0 or not ha_client:
            print(f"House Arrest service failed for {app_id}, code={res}")
            return None

        res = self.lib.house_arrest_send_command(ha_client, b"VendDocuments")
        if res != 0:
            print(f"House Arrest send_command failed for {app_id}, code={res}")
            return None

        if self.lib.house_arrest_get_result(ha_client) != 0:
            return None

        afc_client = self.AFCClient_p()
        if self.lib.afc_client_new_from_house_arrest_client(ha_client, ctypes.byref(afc_client)) != 0:
            return None

        return afc_client

    def is_file_sharing_app(self, afc_client):
        dirlist = ctypes.POINTER(ctypes.c_char_p)()
        res = self.lib.afc_read_directory(afc_client, b"Documents", ctypes.byref(dirlist))
        return res == 0

    @staticmethod
    def list_installed_apps():
        result = subprocess.run(["ideviceinstaller", "-l", "-o", "list_user"],
                                capture_output=True, text=True)
        apps = []
        for line in result.stdout.splitlines():
            if line.strip() and not line.startswith("CFBundleIdentifier"):
                parts = line.split(",")
                if len(parts) >= 3:
                    bundle_id = parts[0].strip()
                    name = parts[2].strip().strip('"')
                    apps.append({"bundle_id": bundle_id, "name": name})
        return apps

    # --- New File Operations ---
    def read_file(self, afc_client, path: str) -> bytes:
        handle = ctypes.c_uint64()
        if self.lib.afc_file_open(afc_client, path.encode("utf-8"), 1, ctypes.byref(handle)) != 0:
            raise RuntimeError("Failed to open file for reading")

        buf = ctypes.create_string_buffer(4096)
        data = b""
        read_bytes = ctypes.c_uint32()

        while True:
            res = self.lib.afc_file_read(afc_client, handle, buf, len(buf), ctypes.byref(read_bytes))
            if res != 0 or read_bytes.value == 0:
                break
            data += buf.raw[:read_bytes.value]

        self.lib.afc_file_close(afc_client, handle)
        return data

    def write_file(self, afc_client, path: str, content: bytes):
        handle = ctypes.c_uint64()
        if self.lib.afc_file_open(afc_client, path.encode("utf-8"), 2, ctypes.byref(handle)) != 0:
            raise RuntimeError("Failed to open file for writing")

        written = ctypes.c_uint32()
        res = self.lib.afc_file_write(afc_client, handle, content, len(content), ctypes.byref(written))
        if res != 0 or written.value != len(content):
            raise RuntimeError("Failed to write file")

        self.lib.afc_file_close(afc_client, handle)

    def create_folder(self, afc_client, path: str):
        if self.lib.afc_make_directory(afc_client, path.encode("utf-8")) != 0:
            raise RuntimeError("Failed to create folder")

    def delete_path(self, afc_client, path: str):
        if self.lib.afc_remove_path(afc_client, path.encode("utf-8")) != 0:
            raise RuntimeError("Failed to delete path")