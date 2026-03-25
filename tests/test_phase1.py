import sys
import os
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.iphone_mtp_wrapper import iPhoneMTPWrapper, usbmuxd_device_info
import ctypes

print("=== Checking structure offsets ===")
print("usbmuxd_device_info size:", ctypes.sizeof(usbmuxd_device_info))
print("handle offset:", usbmuxd_device_info.handle.offset)
print("product_id offset:", usbmuxd_device_info.product_id.offset)
print("udid offset:", usbmuxd_device_info.udid.offset)
print("conn_type offset:", usbmuxd_device_info.conn_type.offset)
print()

DLL_DIR = r"C:\Users\GLC\python projects\iPhoneMTP\libs"
print("Creating wrapper...", flush=True)
wrapper = iPhoneMTPWrapper(dll_dir=DLL_DIR)
print("Wrapper created.\n", flush=True)

# 1. Device detection
print("Listing devices...", flush=True)
udids = wrapper.list_devices()
print("Connected devices:", udids, flush=True)
if not udids:
    print("No iPhone detected. Make sure it's connected and trusted.")
    sys.exit(1)

udid = udids[0]
print(f"Using UDID: {udid}")

# 2. Device name
print("Getting device name...", flush=True)
name = wrapper.get_device_name(udid)
print("Device Name:", name, flush=True)
# getting device properties
ios_ver = wrapper.get_device_property(udid, "ProductVersion")
print(f"iOS Version: {ios_ver}")
model = wrapper.get_device_property(udid, "ProductType")
print(f"Model: {model}")
serial = wrapper.get_device_property(udid, "SerialNumber")
print(f"Serial: {serial}")

# 3. AFC connection
print("Connecting AFC...", flush=True)
afc = wrapper.connect_afc(udid)
if not afc:
    print("Failed to connect AFC")
    sys.exit(1)
print("AFC connected.\n")

# 4. List root folders
print("Listing root AFC folders...", flush=True)
root = wrapper.afc_list_dir(afc, "/")
print("Root AFC folders:", root, flush=True)

# 5. (Optional) Download first photo from DCIM
if "DCIM" in root:
    print("\nChecking DCIM...", flush=True)
    dcim_folders = wrapper.afc_list_dir(afc, "/DCIM")
    if dcim_folders:
        # Usually the first folder is like "100APPLE"
        first_folder = dcim_folders[0]
        print(f"DCIM subfolder: {first_folder}")
        photos = wrapper.afc_list_dir(afc, f"/DCIM/{first_folder}")
        if photos:
            for f in photos:
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.heic')):
                    remote = f"/DCIM/{first_folder}/{f}"
                    local = os.path.join(os.environ['TEMP'], f)
                    print(f"Downloading {f}...", flush=True)
                    if wrapper.afc_download_file(afc, remote, local):
                        print(f"✅ Downloaded {f} to {local}")
                    else:
                        print(f"❌ Failed to download {f}")
                    break
        else:
            print("No photos found in DCIM")
    else:
        print("No DCIM subfolders found")
else:
    print("DCIM folder not present.")

print("\n✅ Test completed.")