# device_manager.py
from integration.libimobiledevice_wrapper import LibIMobileDeviceWrapper

class DeviceManager:
    def detect_devices(self):
        devices = LibIMobileDeviceWrapper.list_devices()
        return [d for d in devices if d]

    def get_info(self, udid):
        return LibIMobileDeviceWrapper.get_device_info(udid)