from ok.device.DeviceManager import DeviceManager as BaseDeviceManager
from ok.device.x11 import X11ForegroundInteraction, X11RegionCaptureMethod, X11Window, find_x11_windows
from ok.gui.Communicate import communicate
from ok.util.logger import Logger
from src.platform_compat import IS_LINUX

logger = Logger.get_logger(__name__)


class LinuxX11DeviceManager(BaseDeviceManager):
    def __init__(self, app_config, exit_event=None, global_config=None):
        super().__init__(app_config, exit_event, global_config)
        self.linux_x11_config = app_config.get("linux_x11")
        if self.linux_x11_config is None:
            return

        self.config.default.setdefault("selected_x11_window", 0)
        if "selected_x11_window" not in self.config:
            self.config["selected_x11_window"] = 0

        capture_methods = self.linux_x11_config.get("capture_method") or ["X11Region"]
        if self.config.get("capture") not in capture_methods:
            self.config["capture"] = capture_methods[0]

        interactions = self.linux_x11_config.get("interaction") or ["X11Foreground"]
        if isinstance(interactions, str):
            interactions = [interactions]
        if self.config.get("interaction") not in interactions:
            self.config["interaction"] = interactions[0]

    def get_devices(self):
        devices = list(self.device_dict.values())
        if IS_LINUX:
            order = {"linux_x11": 0, "adb": 1, "browser": 2, "windows": 3}
        else:
            order = {"adb": 0, "windows": 1, "browser": 2, "linux_x11": 3}

        return sorted(devices, key=lambda item: order.get(item.get("device"), 4))

    def update_pc_device(self):
        imei = None
        if self.linux_x11_config is not None:
            imei = self.update_linux_x11_device()
        if self.windows_capture_config is not None:
            return super().update_pc_device()
        return imei

    def update_linux_x11_device(self):
        for key in list(self.device_dict):
            if key == "x11" or key.startswith("x11_"):
                del self.device_dict[key]

        selected = int(self.config.get("selected_x11_window") or 0)
        windows = find_x11_windows(
            title=self.linux_x11_config.get("title"),
            wm_class=self.linux_x11_config.get("wm_class"),
            selected_window=selected,
        )
        info = windows[0] if windows else None

        if info is None:
            imei = "x11"
            self.device_dict[imei] = {
                "address": "",
                "imei": imei,
                "device": "linux_x11",
                "model": "",
                "nick": "Wuthering Waves (X11)",
                "width": 0,
                "height": 0,
                "hwnd": "Wuthering Waves (X11)",
                "capture": "linux_x11",
                "connected": False,
                "real_hwnd": 0,
                "resolution": "",
            }
            return imei

        imei = f"x11_{info.window_id}"
        nick = info.title or info.wm_class or f"X11-{info.window_id}"
        self.device_dict[imei] = {
            "address": "",
            "imei": imei,
            "device": "linux_x11",
            "model": "",
            "nick": nick,
            "width": info.width,
            "height": info.height,
            "hwnd": nick,
            "capture": "linux_x11",
            "connected": True,
            "real_hwnd": info.window_id,
            "wm_class": info.wm_class,
            "resolution": f"{info.width}x{info.height}",
        }
        return imei

    def set_preferred_device(self, imei=None, index=-1):
        device = None
        if index != -1:
            devices = self.get_devices()
            if 0 <= index < len(devices):
                device = devices[index]
        elif imei is not None:
            device = self.device_dict.get(imei)

        if device and device.get("device") == "linux_x11":
            self.config["selected_x11_window"] = int(device.get("real_hwnd") or 0)

        return super().set_preferred_device(imei, index)

    def do_start(self):
        preferred = self.get_preferred_device()
        if preferred and preferred.get("device") == "linux_x11":
            self.start_linux_x11(preferred)
            communicate.adb_devices.emit(True)
            return
        return super().do_start()

    def start_linux_x11(self, preferred):
        if preferred.get("real_hwnd"):
            self.config["selected_x11_window"] = int(preferred.get("real_hwnd") or 0)

        if not isinstance(self.hwnd_window, X11Window):
            if self.hwnd_window is not None and hasattr(self.hwnd_window, "stop"):
                self.hwnd_window.stop()
            self.hwnd_window = X11Window(
                self.exit_event,
                device_manager=self,
                title=self.linux_x11_config.get("title"),
                wm_class=self.linux_x11_config.get("wm_class"),
            )
        else:
            self.hwnd_window.update_window(
                title=self.linux_x11_config.get("title"),
                wm_class=self.linux_x11_config.get("wm_class"),
            )

        self.hwnd_window.do_update_window_size()
        self.use_linux_x11_capture()
        preferred["connected"] = self.capture_method is not None and self.capture_method.connected()
        if self.hwnd_window.width and self.hwnd_window.height:
            preferred["width"] = self.hwnd_window.width
            preferred["height"] = self.hwnd_window.height
            preferred["resolution"] = f"{self.hwnd_window.width}x{self.hwnd_window.height}"

    def use_linux_x11_capture(self):
        capture_methods = self.linux_x11_config.get("capture_method") or ["X11Region"]
        selected_method = self.config.get("capture")
        if selected_method not in capture_methods:
            selected_method = capture_methods[0]
            self.config["capture"] = selected_method

        if selected_method != "X11Region":
            logger.error(f"unsupported Linux capture method {selected_method}")
            self.capture_method = None
            return

        if not isinstance(self.capture_method, X11RegionCaptureMethod):
            if self.capture_method is not None:
                self.capture_method.close()
            self.capture_method = X11RegionCaptureMethod(self.hwnd_window)
        else:
            self.capture_method.hwnd_window = self.hwnd_window
        self.capture_method.exit_event = self.exit_event

        if not isinstance(self.interaction, X11ForegroundInteraction):
            if self.interaction is not None:
                self.interaction.on_destroy()
            self.interaction = X11ForegroundInteraction(self.capture_method, self.hwnd_window)
        else:
            self.interaction.capture = self.capture_method
            self.interaction.hwnd_window = self.hwnd_window

    def set_capture(self, capture):
        preferred = self.get_preferred_device()
        if preferred and preferred.get("device") == "linux_x11":
            if self.config.get("capture") != capture:
                if self.executor:
                    self.executor.stop_current_task()
                self.config["capture"] = capture
                self.start()
            return
        return super().set_capture(capture)

    def set_interaction(self, interaction):
        preferred = self.get_preferred_device()
        if preferred and preferred.get("device") == "linux_x11":
            interaction_name = interaction.__name__ if isinstance(interaction, type) else interaction
            if self.config.get("interaction") != interaction_name:
                if self.executor:
                    self.executor.stop_current_task()
                self.config["interaction"] = interaction_name
                self.start()
            return
        return super().set_interaction(interaction)

    def device_connected(self):
        preferred = self.get_preferred_device()
        if preferred and preferred.get("device") == "linux_x11":
            return True
        return super().device_connected()
