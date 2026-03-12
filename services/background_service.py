import time
from core.device_manager import DeviceManager
from core.explorer_integrator import ExplorerIntegrator

class BackgroundService:
    def __init__(self):
        self.manager = DeviceManager()
        self.integrator = ExplorerIntegrator()

    def run(self):
        print("Background service started...")
        while True:
            devices = self.manager.detect_devices()
            if devices:
                for udid in devices:
                    print(f"Device connected: {udid}")
                    info = self.manager.get_info(udid)
                    print(f"Info for {udid}:\n{info}")

                    # Create mount point + shortcut
                    mount_path = self.integrator.create_mount_point(udid)
                    print(f"Explorer shortcut created at {mount_path}")
            else:
                print("No devices connected.")
            time.sleep(5)