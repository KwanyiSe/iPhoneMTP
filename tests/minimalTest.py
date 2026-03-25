import sys
import os
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.core.iphone_mtp_wrapper import iPhoneMTPWrapper

DLL_DIR = r"C:\Users\GLC\python projects\iPhoneMTP\libs"
wrapper = iPhoneMTPWrapper(dll_dir=DLL_DIR)

udids = wrapper.list_devices()
if not udids:
    print("No iPhone detected.")
    sys.exit(1)

udid = udids[0]
print(f"Using device: {wrapper.get_device_name(udid)} ({udid})")

# Optional: clear cache for a fresh test
cache_file = Path.home() / ".iphone_mtp_cache.json"
if cache_file.exists():
    cache_file.unlink()
    print("Cache cleared.\n")

print("📱 Fetching user apps...")
user_apps = wrapper.list_user_apps(udid)
print(f"Found {len(user_apps)} user apps")

print("\n🔍 Testing apps for file sharing (parallel, may take 10-30 seconds)...")
start = time.time()
sharing = wrapper.list_accessible_apps(udid, use_cache=True)
print(f"\n✅ {len(sharing)} apps support file sharing (free tier):")
for bundle, name, cmd in sharing:
    print(f"  {name} ({bundle}) -> {cmd}")

non_sharing = wrapper.list_non_sharing_apps(udid)
print(f"\n❌ {len(non_sharing)} apps do NOT support file sharing (paid candidates):")
for bundle, name in non_sharing[:10]:
    print(f"  {name} ({bundle})")
if len(non_sharing) > 10:
    print(f"  ... and {len(non_sharing)-10} more")

print(f"\n⏱️  Test took {time.time()-start:.1f} seconds")
print(f"\n💾 Cache saved to: {cache_file}")

# After the detection loop, pick the first sharing app
if sharing:
    bundle, name, cmd = sharing[0]
    print(f"\n📂 Opening container of {name} ({bundle}) using {cmd}...")
    afc, house, used = wrapper.open_app_container(udid, bundle, use_container_fallback=False)
    if afc:
        print("Connected. Listing Documents folder:")
        files = wrapper.afc_list_dir(afc, "/Documents")
        if files:
            for f in files[:5]:
                print(f"  {f}")
        else:
            print("  (empty)")
        wrapper._libimobiledevice.afc_client_free(afc)
        wrapper._libimobiledevice.house_arrest_client_free(house)
    else:
        print("Failed to open container.")