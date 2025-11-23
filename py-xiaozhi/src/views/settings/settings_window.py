import os
from pathlib import Path

from PyQt5.QtWidgets import (
    QDialog,
    QMessageBox,
    QPushButton,
    QTabWidget,
)

from src.utils.config_manager import ConfigManager
from src.utils.logging_config import get_logger
from src.views.settings.components.audio import AudioWidget
from src.views.settings.components.camera import CameraWidget
from src.views.settings.components.shortcuts_settings import ShortcutsSettingsWidget
from src.views.settings.components.system_options import SystemOptionsWidget
from src.views.settings.components.wake_word import WakeWordWidget


class SettingsWindow(QDialog):
    """
    Cấu hình.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.config_manager = ConfigManager.get_instance()

        # 组件引用
        self.system_options_tab = None
        self.wake_word_tab = None
        self.camera_tab = None
        self.audio_tab = None
        self.shortcuts_tab = None

        # UI控件
        self.ui_controls = {}

        # 初始化UI
        self._setup_ui()
        self._connect_events()

    def _setup_ui(self):
        """
        Thiết lập giao diện UI.
        """
        try:
            from PyQt5 import uic

            ui_path = Path(__file__).parent / "settings_window.ui"
            uic.loadUi(str(ui_path), self)

            # 获取UI控件的引用
            self._get_ui_controls()

            # 添加各个组件选项卡
            self._add_component_tabs()

        except Exception as e:
            self.logger.error(f"Thiết lập UI thất bại: {e}", exc_info=True)
            raise

    def _add_component_tabs(self):
        """
        Thêm các thẻ thành phần.
        """
        try:
            # 获取TabWidget
            tab_widget = self.findChild(QTabWidget, "tabWidget")
            if not tab_widget:
                self.logger.error("Không tìm thấy điều khiển TabWidget")
                return

            # 清空现有选项卡（如果有的话）
            tab_widget.clear()

            # 创建并添加系统选项组件
            self.system_options_tab = SystemOptionsWidget()
            tab_widget.addTab(self.system_options_tab, "Tùy chọn")
            self.system_options_tab.settings_changed.connect(self._on_settings_changed)

            # 创建并添加唤醒词组件
            self.wake_word_tab = WakeWordWidget()
            tab_widget.addTab(self.wake_word_tab, "Từ đánh thức")
            self.wake_word_tab.settings_changed.connect(self._on_settings_changed)

            # 创建并添加摄像头组件
            self.camera_tab = CameraWidget()
            tab_widget.addTab(self.camera_tab, "Camera")
            self.camera_tab.settings_changed.connect(self._on_settings_changed)

            # 创建并添加音频设备组件
            self.audio_tab = AudioWidget()
            tab_widget.addTab(self.audio_tab, "Âm thanh")
            self.audio_tab.settings_changed.connect(self._on_settings_changed)

            # 创建并添加快捷键设置组件
            self.shortcuts_tab = ShortcutsSettingsWidget()
            tab_widget.addTab(self.shortcuts_tab, "Phím tắt")
            self.shortcuts_tab.settings_changed.connect(self._on_settings_changed)

            self.logger.debug("Đã thêm thành công tất cả các thẻ thành phần")

        except Exception as e:
            self.logger.error(f"Thêm thẻ thành phần thất bại: {e}", exc_info=True)

    def _on_settings_changed(self):
        """
        Gọi lại khi thay đổi cài đặt.
        """
        # 可以在此添加一些提示或者其他逻辑

    def _get_ui_controls(self):
        """
        Lấy tham chiếu điều khiển UI.
        """
        # 只需要获取主要的按钮控件
        self.ui_controls.update(
            {
                "save_btn": self.findChild(QPushButton, "save_btn"),
                "cancel_btn": self.findChild(QPushButton, "cancel_btn"),
                "reset_btn": self.findChild(QPushButton, "reset_btn"),
            }
        )

    def _connect_events(self):
        """
        Kết nối xử lý sự kiện.
        """
        if self.ui_controls["save_btn"]:
            self.ui_controls["save_btn"].clicked.connect(self._on_save_clicked)

        if self.ui_controls["cancel_btn"]:
            self.ui_controls["cancel_btn"].clicked.connect(self.reject)

        if self.ui_controls["reset_btn"]:
            self.ui_controls["reset_btn"].clicked.connect(self._on_reset_clicked)

    # 配置加载现在由各个组件自行处理，不需要在主窗口中处理

    # 移除了不再需要的控件操作方法，现在由各个组件处理

    def _on_save_clicked(self):
        """
        Sự kiện nhấn nút lưu.
        """
        try:
            # 收集所有配置数据
            success = self._save_all_config()

            if success:
                # 显示保存成功并提示重启
                reply = QMessageBox.question(
                    self,
                    "Lưu cấu hình thành công",
                    "Cấu hình đã được lưu thành công！\n\nĐể cấu hình có hiệu lực, nên khởi động lại phần mềm。\nBạn có muốn khởi động lại ngay bây giờ không？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )

                if reply == QMessageBox.Yes:
                    self._restart_application()
                else:
                    self.accept()
            else:
                QMessageBox.warning(self, "Lỗi", "Lưu cấu hình thất bại, vui lòng kiểm tra giá trị nhập vào。")

        except Exception as e:
            self.logger.error(f"Lưu cấu hình thất bại: {e}", exc_info=True)
            QMessageBox.critical(self, "Lỗi", f"Đã xảy ra lỗi khi lưu cấu hình: {str(e)}")

    def _save_all_config(self) -> bool:
        """
        Lưu tất cả cấu hình.
        """
        try:
            # 从各个组件收集配置数据
            all_config_data = {}

            # 系统选项配置
            if self.system_options_tab:
                system_config = self.system_options_tab.get_config_data()
                all_config_data.update(system_config)

            # 唤醒词配置
            if self.wake_word_tab:
                wake_word_config = self.wake_word_tab.get_config_data()
                all_config_data.update(wake_word_config)
                # 保存唤醒词文件
                self.wake_word_tab.save_keywords()

            # 摄像头配置
            if self.camera_tab:
                camera_config = self.camera_tab.get_config_data()
                all_config_data.update(camera_config)

            # 音频设备配置
            if self.audio_tab:
                audio_config = self.audio_tab.get_config_data()
                all_config_data.update(audio_config)

            # 快捷键配置
            if self.shortcuts_tab:
                # 快捷键组件有自己的保存方法
                self.shortcuts_tab.apply_settings()

            # 批量更新配置
            for config_path, value in all_config_data.items():
                self.config_manager.update_config(config_path, value)

            self.logger.info("Lưu cấu hình thành công")
            return True

        except Exception as e:
            self.logger.error(f"Lỗi khi lưu cấu hình: {e}", exc_info=True)
            return False

    def _on_reset_clicked(self):
        """
        Sự kiện nhấn nút đặt lại.
        """
        reply = QMessageBox.question(
            self,
            "Xác nhận đặt lại",
            "Bạn có chắc chắn muốn đặt lại tất cả cấu hình về mặc định không？\nĐiều này sẽ xóa tất cả cài đặt hiện tại。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self._reset_to_defaults()

    def _reset_to_defaults(self):
        """
        Đặt lại về mặc định.
        """
        try:
            # 让各个组件重置为默认值
            if self.system_options_tab:
                self.system_options_tab.reset_to_defaults()

            if self.wake_word_tab:
                self.wake_word_tab.reset_to_defaults()

            if self.camera_tab:
                self.camera_tab.reset_to_defaults()

            if self.audio_tab:
                self.audio_tab.reset_to_defaults()

            if self.shortcuts_tab:
                self.shortcuts_tab.reset_to_defaults()

            self.logger.info("Tất cả cấu hình thành phần đã được đặt lại về mặc định")

        except Exception as e:
            self.logger.error(f"Đặt lại cấu hình thất bại: {e}", exc_info=True)
            QMessageBox.critical(self, "Lỗi", f"Đã xảy ra lỗi khi đặt lại cấu hình: {str(e)}")

    def _restart_application(self):
        """
        Khởi động lại ứng dụng.
        """
        try:
            self.logger.info("Người dùng chọn khởi động lại ứng dụng")

            # 关闭设置窗口
            self.accept()

            # 直接重启程序
            self._direct_restart()

        except Exception as e:
            self.logger.error(f"Khởi động lại ứng dụng thất bại: {e}", exc_info=True)
            QMessageBox.warning(
                self, "Khởi động lại thất bại", "Tự động khởi động lại thất bại, vui lòng khởi động lại phần mềm thủ công để cấu hình có hiệu lực。"
            )

    def _direct_restart(self):
        """
        Khởi động lại chương trình trực tiếp.
        """
        try:
            import sys

            from PyQt5.QtWidgets import QApplication

            # 获取当前执行的程序路径和参数
            python = sys.executable
            script = sys.argv[0]
            args = sys.argv[1:]

            self.logger.info(f"Lệnh khởi động lại: {python} {script} {' '.join(args)}")

            # 关闭当前应用
            QApplication.quit()

            # 启动新实例
            if getattr(sys, "frozen", False):
                # 打包环境
                os.execv(sys.executable, [sys.executable] + args)
            else:
                # 开发环境
                os.execv(python, [python, script] + args)

        except Exception as e:
            self.logger.error(f"Khởi động lại trực tiếp thất bại: {e}", exc_info=True)

    def closeEvent(self, event):
        """
        窗口关闭事件.
        """
        self.logger.debug("Cửa sổ cài đặt đã đóng")
        super().closeEvent(event)
