import sys
import os
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.iphone_mtp_wrapper import iPhoneMTPWrapper, usbmuxd_device_info
import ctypes

print("Structure size and offsets:")
print("size =", ctypes.sizeof(usbmuxd_device_info))
print("handle offset:", usbmuxd_device_info.handle.offset)
print("product_id offset:", usbmuxd_device_info.product_id.offset)
print("udid offset:", usbmuxd_device_info.udid.offset)
print("conn_type offset:", usbmuxd_device_info.conn_type.offset)
print()

DLL_DIR = r"C:\Users\GLC\python projects\iPhoneMTP\libs"
print("Creating wrapper...", flush=True)
wrapper = iPhoneMTPWrapper(dll_dir=DLL_DIR)
print("Wrapper created.", flush=True)

print("\nCalling list_devices...", flush=True)
try:
    udids = wrapper.list_devices()
    print("list_devices returned:", udids, flush=True)
except Exception as e:
    print("Exception in list_devices:", flush=True)
    traceback.print_exc()