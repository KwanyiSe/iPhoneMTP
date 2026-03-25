
"""
Low_level wrapper for libimobiledevice DLLs.
Provides device detection, AFC, and file operations.

"""

import ctypes
import os
from ctypes import (
    c_void_p, c_char_p, c_int, c_uint32, c_uint8, c_uint64, c_char,
    POINTER, byref, create_string_buffer
)
from typing import List, Optional


class usbmuxd_device_info(ctypes.Structure):
    _fields_ = [
        ("handle", c_uint32),
        ("product_id", c_uint32),
        ("udid", c_char * 256),
        ("conn_type", c_uint8),
    ]


class iPhoneMTPWrapper:
    def __init__(self, dll_dir: Optional[str] = None):
        self._dll_dir = dll_dir
        self._libusbmuxd = None
        self._libimobiledevice = None
        self._libplist = None
        self._libc = None
        self._load_dlls()
        self._define_functions()

    # =========================
    # DLL LOADING
    # =========================
    def _load_dlls(self):
        if self._dll_dir:
            dll_dir = os.path.abspath(self._dll_dir)
            os.add_dll_directory(dll_dir)
            libusbmuxd_path = os.path.join(dll_dir, "libusbmuxd-2.0.dll")
            libimobiledevice_path = os.path.join(dll_dir, "libimobiledevice-1.0.dll")
            libplist_path = os.path.join(dll_dir, "libplist-2.0.dll")
        else:
            libusbmuxd_path = "libusbmuxd-2.0.dll"
            libimobiledevice_path = "libimobiledevice-1.0.dll"
            libplist_path = "libplist-2.0.dll"

        self._libusbmuxd = ctypes.CDLL(libusbmuxd_path)
        self._libimobiledevice = ctypes.CDLL(libimobiledevice_path)
        self._libplist = ctypes.CDLL(libplist_path)
        self._libc = ctypes.CDLL("msvcrt.dll")  # C runtime for free() (currently unused)

    def _define_functions(self):
        # libusbmuxd
        self._libusbmuxd.usbmuxd_get_device_list.argtypes = [
            POINTER(POINTER(usbmuxd_device_info)), c_int
        ]
        self._libusbmuxd.usbmuxd_get_device_list.restype = c_int
        self._libusbmuxd.usbmuxd_device_list_free.argtypes = [
            POINTER(usbmuxd_device_info)
        ]
        self._libusbmuxd.usbmuxd_device_list_free.restype = None

        # libimobiledevice (device & lockdown)
        self._libimobiledevice.idevice_new.argtypes = [
            POINTER(c_void_p), c_char_p
        ]
        self._libimobiledevice.idevice_new.restype = c_int
        self._libimobiledevice.idevice_free.argtypes = [c_void_p]
        self._libimobiledevice.idevice_free.restype = None

        self._libimobiledevice.lockdownd_client_new_with_handshake.argtypes = [
            c_void_p, POINTER(c_void_p), c_char_p
        ]
        self._libimobiledevice.lockdownd_client_new_with_handshake.restype = c_int
        self._libimobiledevice.lockdownd_client_free.argtypes = [c_void_p]
        self._libimobiledevice.lockdownd_client_free.restype = None

        self._libimobiledevice.lockdownd_get_value.argtypes = [
            c_void_p, c_char_p, c_char_p, POINTER(c_void_p)
        ]
        self._libimobiledevice.lockdownd_get_value.restype = c_int

        # AFC
        self._libimobiledevice.afc_client_start_service.argtypes = [
            c_void_p, POINTER(c_void_p), c_char_p
        ]
        self._libimobiledevice.afc_client_start_service.restype = c_int
        self._libimobiledevice.afc_client_free.argtypes = [c_void_p]
        self._libimobiledevice.afc_client_free.restype = c_int

        self._libimobiledevice.afc_read_directory.argtypes = [
            c_void_p, c_char_p, POINTER(POINTER(c_char_p))
        ]
        self._libimobiledevice.afc_read_directory.restype = c_int

        self._libimobiledevice.afc_file_open.argtypes = [
            c_void_p, c_char_p, c_uint32, POINTER(c_uint64)
        ]
        self._libimobiledevice.afc_file_open.restype = c_int

        self._libimobiledevice.afc_file_read.argtypes = [
            c_void_p, c_uint64, c_void_p, c_uint32, POINTER(c_uint32)
        ]
        self._libimobiledevice.afc_file_read.restype = c_int

        self._libimobiledevice.afc_file_write.argtypes = [
            c_void_p, c_uint64, c_void_p, c_uint32, POINTER(c_uint32)
        ]
        self._libimobiledevice.afc_file_write.restype = c_int

        self._libimobiledevice.afc_file_close.argtypes = [
            c_void_p, c_uint64
        ]
        self._libimobiledevice.afc_file_close.restype = c_int

        self._libimobiledevice.afc_make_directory.argtypes = [
            c_void_p, c_char_p
        ]
        self._libimobiledevice.afc_make_directory.restype = c_int

        self._libimobiledevice.afc_remove_path.argtypes = [
            c_void_p, c_char_p
        ]
        self._libimobiledevice.afc_remove_path.restype = c_int

        # libplist
        self._libplist.plist_get_string_val.argtypes = [
            c_void_p, POINTER(c_char_p)
        ]
        self._libplist.plist_get_string_val.restype = None
        self._libplist.plist_free.argtypes = [c_void_p]
        self._libplist.plist_free.restype = None

        # C runtime
        self._libc.free.argtypes = [c_void_p]
        self._libc.free.restype = None

    # =========================
    # DEVICE DETECTION
    # =========================
    def list_devices(self) -> List[str]:
        device_list = POINTER(usbmuxd_device_info)()
        count = self._libusbmuxd.usbmuxd_get_device_list(byref(device_list), 0)
        if count < 0:
            return []

        udids = []
        for i in range(count):
            dev = device_list[i]
            raw = bytes(dev.udid)
            udid_bytes = raw.split(b'\x00', 1)[0]
            udid = udid_bytes.decode('utf-8')
            if udid:
                udids.append(udid)

        # TODO: usbmuxd_device_list_free causes hang – disabled for now
        # self._libusbmuxd.usbmuxd_device_list_free(device_list)
        return udids

    def get_device_name(self, udid: str) -> Optional[str]:
        return self.get_device_property(udid, "DeviceName")

    def get_device_property(self, udid: str, key: str) -> Optional[str]:
        """Retrieve any device property via lockdown (e.g., 'ProductVersion', 'SerialNumber')."""
        device = c_void_p()
        if self._libimobiledevice.idevice_new(byref(device), udid.encode()) != 0:
            return None

        lockdown = c_void_p()
        if self._libimobiledevice.lockdownd_client_new_with_handshake(
            device, byref(lockdown), b"iPhoneMTP"
        ) != 0:
            self._libimobiledevice.idevice_free(device)
            return None

        value = c_void_p()
        if self._libimobiledevice.lockdownd_get_value(
            lockdown, None, key.encode(), byref(value)
        ) != 0:
            self._libimobiledevice.lockdownd_client_free(lockdown)
            self._libimobiledevice.idevice_free(device)
            return None

        result = self._plist_to_string(value)
        self._libplist.plist_free(value)
        self._libimobiledevice.lockdownd_client_free(lockdown)
        self._libimobiledevice.idevice_free(device)
        return result

    def _plist_to_string(self, plist) -> Optional[str]:
        if not plist:
            return None
        s = c_char_p()
        self._libplist.plist_get_string_val(plist, byref(s))
        if s.value:
            result = s.value.decode('utf-8')
            # TODO: free allocated string – disabled because free() from msvcrt causes hang
            # self._libc.free(s.value)
            return result
        return None

    # =========================
    # AFC (SYSTEM FOLDERS)
    # =========================
    def connect_afc(self, udid: str):
        device = c_void_p()
        if self._libimobiledevice.idevice_new(byref(device), udid.encode()) != 0:
            return None

        afc = c_void_p()
        if self._libimobiledevice.afc_client_start_service(
            device, byref(afc), b"iPhoneMTP"
        ) != 0:
            self._libimobiledevice.idevice_free(device)
            return None

        # Store device handle for later cleanup (optional)
        self._afc_device = device
        return afc

    def afc_list_dir(self, afc, path: str = "/"):
        file_list = POINTER(c_char_p)()
        if self._libimobiledevice.afc_read_directory(
            afc, path.encode(), byref(file_list)
        ) != 0:
            return []

        files = []
        i = 0
        while file_list[i]:
            name = file_list[i].decode('utf-8')
            if name not in (".", ".."):
                files.append(name)
            i += 1
        # TODO: free file_list (memory leak)
        return files

    def afc_download_file(self, afc, remote_path: str, local_path: str) -> bool:
        FILE_OPEN_READ = 0x00000001
        handle = c_uint64()
        if self._libimobiledevice.afc_file_open(
            afc, remote_path.encode(), FILE_OPEN_READ, byref(handle)
        ) != 0:
            return False

        local_dir = os.path.dirname(local_path)
        if local_dir and not os.path.exists(local_dir):
            os.makedirs(local_dir, exist_ok=True)

        with open(local_path, 'wb') as f:
            buffer = create_string_buffer(64 * 1024)
            while True:
                bytes_read = c_uint32(0)
                if self._libimobiledevice.afc_file_read(
                    afc, handle.value, buffer, len(buffer), byref(bytes_read)
                ) != 0 or bytes_read.value == 0:
                    break
                f.write(buffer.raw[:bytes_read.value])

        self._libimobiledevice.afc_file_close(afc, handle.value)
        return True

    def afc_upload_file(self, afc, local_path: str, remote_path: str) -> bool:
        if not os.path.exists(local_path):
            return False

        FILE_OPEN_WRITE = 0x00000002
        handle = c_uint64()
        if self._libimobiledevice.afc_file_open(
            afc, remote_path.encode(), FILE_OPEN_WRITE, byref(handle)
        ) != 0:
            return False

        with open(local_path, 'rb') as f:
            buffer = f.read(64 * 1024)
            while buffer:
                bytes_written = c_uint32(0)
                if self._libimobiledevice.afc_file_write(
                    afc, handle.value, buffer, len(buffer), byref(bytes_written)
                ) != 0 or bytes_written.value != len(buffer):
                    self._libimobiledevice.afc_file_close(afc, handle.value)
                    return False
                buffer = f.read(64 * 1024)

        self._libimobiledevice.afc_file_close(afc, handle.value)
        return True

    def afc_delete(self, afc, path: str) -> bool:
        return self._libimobiledevice.afc_remove_path(afc, path.encode()) == 0

    def afc_mkdir(self, afc, path: str) -> bool:
        return self._libimobiledevice.afc_make_directory(afc, path.encode()) == 0