import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from test2 import LibIMobileDeviceWrapper


wrapper = LibIMobileDeviceWrapper()
devices = wrapper.list_devices()
print("Devices:", devices)

if devices and devices[0]:
    udid = devices[0]
    print("Connecting House Arrest for Xender:", udid)
    afc_client = wrapper.connect_house_arrest(udid, "cn.xender")

    # List files in Xender Documents
    files = wrapper.list_folder(afc_client, "")
    print("📂 Files in Xender Documents:", files)

    # Add a real file
    pdf_path = r"C:\Users\GLC\Documents\Unimap_doc\planning and designs\Week1Plan.pdf"
    try:
        wrapper.sync_file(afc_client, pdf_path, "")
        print(f"✅ Synced {pdf_path} into Xender Documents")
    except Exception as e:
        print("Sync failed:", e)

else:
    print("No devices found")