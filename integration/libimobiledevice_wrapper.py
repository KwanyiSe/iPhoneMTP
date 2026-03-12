import subprocess

class LibIMobileDeviceWrapper:
    @staticmethod
    def list_devices():
        result = subprocess.run(["idevice_id.exe", "-l"], capture_output=True, text=True)
        return result.stdout.strip().split("\n") if result.stdout else []

    @staticmethod
    def get_device_info(udid):
        result = subprocess.run(["ideviceinfo.exe", "-u", udid], capture_output=True, text=True)
        return result.stdout if result.stdout else None