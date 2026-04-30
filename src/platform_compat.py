import os
import sys


IS_LINUX = sys.platform.startswith("linux")
IS_WINDOWS = sys.platform == "win32"

_TRUE_VALUES = {"1", "true", "yes", "on"}


def configure_runtime():
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if IS_LINUX:
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
        patch_ok_linux_x11()


def patch_ok_linux_x11():
    try:
        import ok
        import ok.device.DeviceManager as device_manager_module
        import ok.util.file as file_module
        from src.linux_x11_device import LinuxX11DeviceManager

        ok.DeviceManager = LinuxX11DeviceManager
        device_manager_module.DeviceManager = LinuxX11DeviceManager
        ok.install_path_isascii = linux_install_path_isascii
        file_module.install_path_isascii = linux_install_path_isascii
        patch_ok_base_loading()
        patch_ok_start_ui()
    except Exception:
        return


def linux_install_path_isascii():
    return True, os.getcwd()


def patch_ok_base_loading():
    from ok.gui.widget.BaseLoading import BaseLoading

    if getattr(BaseLoading, "_ok_ww_linux_patch", False):
        return

    def base_loading_init(self, *args, **kwargs):
        super(BaseLoading, self).__init__()
        self.loading_dialog = None

    BaseLoading.__init__ = base_loading_init
    BaseLoading._ok_ww_linux_patch = True


def patch_ok_start_ui():
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QListWidgetItem

    from ok import og
    from ok.gui.start.SelectCaptureListView import SelectCaptureListView
    from ok.gui.start.SelectInteractionListView import SelectInteractionListView
    from ok.gui.start.StartTab import StartTab

    if getattr(StartTab, "_ok_ww_linux_patch", False):
        return

    original_capture_index_changed = StartTab.capture_index_changed
    original_interaction_index_changed = StartTab.interaction_index_changed
    original_update_capture = StartTab.update_capture

    def capture_index_changed(self):
        device = og.device_manager.get_preferred_device()
        if device and device.get("device") == "linux_x11":
            methods = og.device_manager.linux_x11_config.get("capture_method", [])
            index = self.capture_list.currentRow()
            if 0 <= index < len(methods):
                og.device_manager.set_capture(methods[index])
            self.start_card.update_status()
            return
        return original_capture_index_changed(self)

    def interaction_index_changed(self):
        device = og.device_manager.get_preferred_device()
        if device and device.get("device") == "linux_x11":
            methods = og.device_manager.linux_x11_config.get("interaction", [])
            if isinstance(methods, str):
                methods = [methods]
            index = self.interaction_list.currentRow()
            if 0 <= index < len(methods):
                og.device_manager.set_interaction(methods[index])
            self.start_card.update_status()
            return
        return original_interaction_index_changed(self)

    def update_capture(self, finished):
        original_update_capture(self, finished)
        for row in range(self.device_list.count()):
            item = self.device_list.item(row)
            device = item.data(Qt.UserRole)
            if device and device.get("device") == "linux_x11":
                connected = self.tr("Connected") if device["connected"] else self.tr("Disconnected")
                item.setText(
                    f"Linux X11 {connected}: {device.get('nick')} {device.get('resolution') or ''}"
                )

    def select_capture_update_for_device(self):
        device = og.device_manager.get_preferred_device()
        if not device or device.get("device") != "linux_x11":
            return self._ok_ww_original_update_for_device()
        self.blockSignals(True)
        methods = og.device_manager.linux_x11_config.get("capture_method", []) or ["X11Region"]
        while self.count() > len(methods):
            self.takeItem(self.count() - 1)
        for index, method in enumerate(methods):
            method_name = method.__name__ if isinstance(method, type) else str(method)
            if index < self.count():
                self.item(index).setText(self.tr(method_name))
            else:
                self.addItem(QListWidgetItem(self.tr(method_name)))
        selected = 0
        current = og.device_manager.get_preferred_capture()
        for index, method in enumerate(methods):
            method_name = method.__name__ if isinstance(method, type) else str(method)
            if current == method_name:
                selected = index
                break
        self.blockSignals(False)
        self.setCurrentRow(selected)

    def select_interaction_update_for_device(self):
        device = og.device_manager.get_preferred_device()
        if not device or device.get("device") != "linux_x11":
            return self._ok_ww_original_update_for_device()
        self.blockSignals(True)
        methods = og.device_manager.linux_x11_config.get("interaction", []) or ["X11Foreground"]
        if isinstance(methods, str):
            methods = [methods]
        while self.count() > len(methods):
            self.takeItem(self.count() - 1)
        for index, method in enumerate(methods):
            method_name = method.__name__ if isinstance(method, type) else str(method)
            if index < self.count():
                self.item(index).setText(self.tr(method_name))
            else:
                self.addItem(QListWidgetItem(self.tr(method_name)))
        selected = 0
        current = og.device_manager.config.get("interaction")
        for index, method in enumerate(methods):
            method_name = method.__name__ if isinstance(method, type) else str(method)
            if current == method_name:
                selected = index
                break
        self.blockSignals(False)
        self.setCurrentRow(selected)

    StartTab.capture_index_changed = capture_index_changed
    StartTab.interaction_index_changed = interaction_index_changed
    StartTab.update_capture = update_capture

    SelectCaptureListView._ok_ww_original_update_for_device = SelectCaptureListView.update_for_device
    SelectCaptureListView.update_for_device = select_capture_update_for_device
    SelectInteractionListView._ok_ww_original_update_for_device = SelectInteractionListView.update_for_device
    SelectInteractionListView.update_for_device = select_interaction_update_for_device

    StartTab._ok_ww_linux_patch = True


def env_flag(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in _TRUE_VALUES


def env_float(name, default):
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default
