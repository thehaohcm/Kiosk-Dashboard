import threading
import time
from pathlib import Path

import numpy as np
import sounddevice as sd
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QWidget,
)

from src.utils.config_manager import ConfigManager
from src.utils.logging_config import get_logger


class AudioWidget(QWidget):
    """
    Thành phần cài đặt thiết bị âm thanh.
    """

    # 信号定义
    settings_changed = pyqtSignal()
    status_message = pyqtSignal(str)
    reset_input_ui = pyqtSignal()
    reset_output_ui = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.config_manager = ConfigManager.get_instance()

        # UI控件引用
        self.ui_controls = {}

        # 设备数据
        self.input_devices = []
        self.output_devices = []

        # 测试状态
        self.testing_input = False
        self.testing_output = False

        # 初始化UI
        self._setup_ui()
        self._connect_events()
        self._scan_devices()
        self._load_config_values()

        # 连接线程安全UI更新信号
        try:
            self.status_message.connect(self._on_status_message)
            self.reset_input_ui.connect(self._reset_input_test_ui)
            self.reset_output_ui.connect(self._reset_output_test_ui)
        except Exception:
            pass

    def _setup_ui(self):
        """
        Thiết lập giao diện UI.
        """
        try:
            from PyQt5 import uic

            ui_path = Path(__file__).parent / "audio_widget.ui"
            uic.loadUi(str(ui_path), self)

            # 获取UI控件引用
            self._get_ui_controls()

        except Exception as e:
            self.logger.error(f"Thiết lập UI âm thanh thất bại: {e}", exc_info=True)
            raise

    def _get_ui_controls(self):
        """
        Lấy tham chiếu điều khiển UI.
        """
        self.ui_controls.update(
            {
                "input_device_combo": self.findChild(QComboBox, "input_device_combo"),
                "output_device_combo": self.findChild(QComboBox, "output_device_combo"),
                "input_info_label": self.findChild(QLabel, "input_info_label"),
                "output_info_label": self.findChild(QLabel, "output_info_label"),
                "test_input_btn": self.findChild(QPushButton, "test_input_btn"),
                "test_output_btn": self.findChild(QPushButton, "test_output_btn"),
                "scan_devices_btn": self.findChild(QPushButton, "scan_devices_btn"),
                "status_text": self.findChild(QTextEdit, "status_text"),
            }
        )

    def _connect_events(self):
        """
        Kết nối xử lý sự kiện.
        """
        # 设备选择变更
        if self.ui_controls["input_device_combo"]:
            self.ui_controls["input_device_combo"].currentTextChanged.connect(
                self._on_input_device_changed
            )

        if self.ui_controls["output_device_combo"]:
            self.ui_controls["output_device_combo"].currentTextChanged.connect(
                self._on_output_device_changed
            )

        # 按钮点击
        if self.ui_controls["test_input_btn"]:
            self.ui_controls["test_input_btn"].clicked.connect(self._test_input_device)

        if self.ui_controls["test_output_btn"]:
            self.ui_controls["test_output_btn"].clicked.connect(
                self._test_output_device
            )

        if self.ui_controls["scan_devices_btn"]:
            self.ui_controls["scan_devices_btn"].clicked.connect(self._scan_devices)

    def _on_input_device_changed(self):
        """
        Sự kiện thay đổi thiết bị đầu vào.
        """
        self.settings_changed.emit()
        self._update_device_info()

    def _on_output_device_changed(self):
        """
        Sự kiện thay đổi thiết bị đầu ra.
        """
        self.settings_changed.emit()
        self._update_device_info()

    def _update_device_info(self):
        """
        Cập nhật thông tin hiển thị thiết bị.
        """
        try:
            # 更新输入设备信息
            input_device_id = self.ui_controls["input_device_combo"].currentData()
            if input_device_id is not None:
                input_device = next(
                    (d for d in self.input_devices if d["id"] == input_device_id), None
                )
                if input_device:
                    info_text = f"Tần số lấy mẫu: {int(input_device['sample_rate'])}Hz, kênh: {input_device['channels']}"
                    self.ui_controls["input_info_label"].setText(info_text)
                else:
                    self.ui_controls["input_info_label"].setText("Không thể lấy thông tin thiết bị")
            else:
                self.ui_controls["input_info_label"].setText("Chưa chọn thiết bị")

            # 更新输出设备信息
            output_device_id = self.ui_controls["output_device_combo"].currentData()
            if output_device_id is not None:
                output_device = next(
                    (d for d in self.output_devices if d["id"] == output_device_id),
                    None,
                )
                if output_device:
                    info_text = f"Tần số lấy mẫu: {int(output_device['sample_rate'])}Hz, kênh: {output_device['channels']}"
                    self.ui_controls["output_info_label"].setText(info_text)
                else:
                    self.ui_controls["output_info_label"].setText("Không thể lấy thông tin thiết bị")
            else:
                self.ui_controls["output_info_label"].setText("Chưa chọn thiết bị")

        except Exception as e:
            self.logger.error(f"更新设备信息失败: {e}", exc_info=True)

    def _scan_devices(self):
        """
        Quét thiết bị âm thanh.
        """
        try:
            self._append_status("Đang quét thiết bị âm thanh...")

            # 清空现有设备列表
            self.input_devices.clear()
            self.output_devices.clear()

            # 获取系统默认设备
            default_input = sd.default.device[0] if sd.default.device else None
            default_output = sd.default.device[1] if sd.default.device else None

            # 扫描所有设备
            devices = sd.query_devices()
            for i, dev_info in enumerate(devices):
                device_name = dev_info["name"]

                # 添加输入设备
                if dev_info["max_input_channels"] > 0:
                    default_mark = " (mặc định)" if i == default_input else ""
                    self.input_devices.append(
                        {
                            "id": i,
                            "name": device_name + default_mark,
                            "raw_name": device_name,
                            "channels": dev_info["max_input_channels"],
                            "sample_rate": dev_info["default_samplerate"],
                        }
                    )

                # 添加输出设备
                if dev_info["max_output_channels"] > 0:
                    default_mark = " (mặc định)" if i == default_output else ""
                    self.output_devices.append(
                        {
                            "id": i,
                            "name": device_name + default_mark,
                            "raw_name": device_name,
                            "channels": dev_info["max_output_channels"],
                            "sample_rate": dev_info["default_samplerate"],
                        }
                    )

            # 更新下拉框
            self._update_device_combos()

            # 自动选择默认设备
            self._select_default_devices()

            self._append_status(
                f"Quét hoàn tất: Tìm thấy {len(self.input_devices)} thiết bị đầu vào, {len(self.output_devices)} thiết bị đầu ra"
            )

        except Exception as e:
            self.logger.error(f"Quét thiết bị âm thanh thất bại: {e}", exc_info=True)
            self._append_status(f"Quét thiết bị thất bại: {str(e)}")

    def _update_device_combos(self):
        """
        Cập nhật hộp thoại thả xuống thiết bị.
        """
        try:
            # 保存当前选择
            current_input = self.ui_controls["input_device_combo"].currentData()
            current_output = self.ui_controls["output_device_combo"].currentData()

            # 清空并重新填充输入设备
            self.ui_controls["input_device_combo"].clear()
            for device in self.input_devices:
                self.ui_controls["input_device_combo"].addItem(
                    device["name"], device["id"]
                )

            # 清空并重新填充输出设备
            self.ui_controls["output_device_combo"].clear()
            for device in self.output_devices:
                self.ui_controls["output_device_combo"].addItem(
                    device["name"], device["id"]
                )

            # 尝试恢复之前的选择
            if current_input is not None:
                index = self.ui_controls["input_device_combo"].findData(current_input)
                if index >= 0:
                    self.ui_controls["input_device_combo"].setCurrentIndex(index)

            if current_output is not None:
                index = self.ui_controls["output_device_combo"].findData(current_output)
                if index >= 0:
                    self.ui_controls["output_device_combo"].setCurrentIndex(index)

        except Exception as e:
            self.logger.error(f"更新设备下拉框失败: {e}", exc_info=True)

    def _select_default_devices(self):
        """
        自动选择默认设备（与audio_codec.py的逻辑保持一致）。
        """
        try:
            # 优先选择配置中的设备，如果没有则选择系统默认设备
            config_input_id = self.config_manager.get_config(
                "AUDIO_DEVICES.input_device_id"
            )
            config_output_id = self.config_manager.get_config(
                "AUDIO_DEVICES.output_device_id"
            )

            # 选择输入设备
            if config_input_id is not None:
                # 使用配置中的设备
                index = self.ui_controls["input_device_combo"].findData(config_input_id)
                if index >= 0:
                    self.ui_controls["input_device_combo"].setCurrentIndex(index)
            else:
                # 自动选择默认输入设备（带"默认"标记的）
                for i in range(self.ui_controls["input_device_combo"].count()):
                    if "mặc định" in self.ui_controls["input_device_combo"].itemText(i):
                        self.ui_controls["input_device_combo"].setCurrentIndex(i)
                        break

            # 选择输出设备
            if config_output_id is not None:
                # 使用配置中的设备
                index = self.ui_controls["output_device_combo"].findData(
                    config_output_id
                )
                if index >= 0:
                    self.ui_controls["output_device_combo"].setCurrentIndex(index)
            else:
                # 自动选择默认输出设备（带"默认"标记的）
                for i in range(self.ui_controls["output_device_combo"].count()):
                    if "mặc định" in self.ui_controls["output_device_combo"].itemText(i):
                        self.ui_controls["output_device_combo"].setCurrentIndex(i)
                        break

            # 更新设备信息显示
            self._update_device_info()

        except Exception as e:
            self.logger.error(f"选择默认设备失败: {e}", exc_info=True)

    def _test_input_device(self):
        """
        Kiểm tra thiết bị đầu vào.
        """
        if self.testing_input:
            return

        try:
            device_id = self.ui_controls["input_device_combo"].currentData()
            if device_id is None:
                QMessageBox.warning(self, "Nhắc nhở", "Vui lòng chọn trước thiết bị đầu vào")
                return

            self.testing_input = True
            self.ui_controls["test_input_btn"].setEnabled(False)
            self.ui_controls["test_input_btn"].setText("Đang ghi âm...")

            # 在线程中执行测试
            test_thread = threading.Thread(
                target=self._do_input_test, args=(device_id,)
            )
            test_thread.daemon = True
            test_thread.start()

        except Exception as e:
            self.logger.error(f"测试输入设备失败: {e}", exc_info=True)
            self._append_status(f"Kiểm tra thiết bị đầu vào thất bại: {str(e)}")
            self._reset_input_test_ui()

    def _do_input_test(self, device_id):
        """
        Thực hiện kiểm tra thiết bị đầu vào.
        """
        try:
            # 获取设备信息和采样率
            input_device = next(
                (d for d in self.input_devices if d["id"] == device_id), None
            )
            if not input_device:
                self._append_status_threadsafe("Lỗi: Không thể lấy thông tin thiết bị")
                return

            sample_rate = int(input_device["sample_rate"])
            duration = 3  # 录音时长3秒

            self._append_status_threadsafe(
                f"开始录音测试 (设备: {device_id}, 采样率: {sample_rate}Hz)"
            )
            self._append_status_threadsafe("Vui lòng nói vào micrô, ví dụ đếm số: 1, 2, 3...")

            # 倒计时提示
            for i in range(3, 0, -1):
                self._append_status_threadsafe(f"Bắt đầu ghi âm sau {i} giây...")
                time.sleep(1)

            self._append_status_threadsafe("Đang ghi âm, vui lòng nói... (3 giây)")

            # 录音
            recording = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                device=device_id,
                dtype=np.float32,
            )
            sd.wait()

            self._append_status_threadsafe("录音完成，正在分析...")

            # 分析录音质量
            max_amplitude = np.max(np.abs(recording))
            rms = np.sqrt(np.mean(recording**2))

            # 检测是否有语音活动
            frame_length = int(0.1 * sample_rate)  # 100ms帧
            frames = []
            for i in range(0, len(recording) - frame_length, frame_length):
                frame_rms = np.sqrt(np.mean(recording[i : i + frame_length] ** 2))
                frames.append(frame_rms)

            active_frames = sum(1 for f in frames if f > 0.01)  # 活跃帧数
            activity_ratio = active_frames / len(frames) if frames else 0

            # 测试结果分析
            if max_amplitude < 0.001:
                self._append_status_threadsafe("[Thất bại] Không phát hiện tín hiệu âm thanh")
                self._append_status_threadsafe(
                    "Vui lòng kiểm tra: 1) Kết nối micrô 2) Âm lượng hệ thống 3) Quyền micrô"
                )
            elif max_amplitude > 0.8:
                self._append_status_threadsafe("[Cảnh báo] Tín hiệu âm thanh quá tải")
                self._append_status_threadsafe("Khuyến nghị giảm khuếch đại micrô hoặc cài đặt âm lượng")
            elif activity_ratio < 0.1:
                self._append_status_threadsafe("[Cảnh báo] Đã phát hiện âm thanh nhưng hoạt động giọng nói ít")
                self._append_status_threadsafe(
                    "Đảm bảo nói vào micrô, hoặc kiểm tra độ nhạy micrô"
                )
            else:
                self._append_status_threadsafe("[Thành công] Kiểm tra ghi âm đã vượt qua")
                self._append_status_threadsafe(
                    f"Dữ liệu chất lượng âm thanh: Âm lượng tối đa={max_amplitude:.1%}, Âm lượng trung bình={rms:.1%}, Độ hoạt động={activity_ratio:.1%}"
                )
                self._append_status_threadsafe("Micrô hoạt động bình thường")

        except Exception as e:
            self.logger.error(f"录音测试失败: {e}", exc_info=True)
            self._append_status_threadsafe(f"[Lỗi] Kiểm tra ghi âm thất bại: {str(e)}")
            if "Permission denied" in str(e) or "access" in str(e).lower():
                self._append_status_threadsafe(
                    "Có thể là vấn đề quyền, vui lòng kiểm tra cài đặt quyền micrô hệ thống"
                )
        finally:
            # 重置UI状态（切回主线程）
            self._reset_input_ui_threadsafe()

    def _test_output_device(self):
        """
        Kiểm tra thiết bị đầu ra.
        """
        if self.testing_output:
            return

        try:
            device_id = self.ui_controls["output_device_combo"].currentData()
            if device_id is None:
                QMessageBox.warning(self, "Nhắc nhở", "Vui lòng chọn trước thiết bị đầu ra")
                return

            self.testing_output = True
            self.ui_controls["test_output_btn"].setEnabled(False)
            self.ui_controls["test_output_btn"].setText("Đang phát...")

            # 在线程中执行测试
            test_thread = threading.Thread(
                target=self._do_output_test, args=(device_id,)
            )
            test_thread.daemon = True
            test_thread.start()

        except Exception as e:
            self.logger.error(f"测试输出设备失败: {e}", exc_info=True)
            self._append_status(f"Kiểm tra thiết bị đầu ra thất bại: {str(e)}")
            self._reset_output_test_ui()

    def _do_output_test(self, device_id):
        """
        Thực hiện kiểm tra thiết bị đầu ra.
        """
        try:
            # 获取设备信息和采样率
            output_device = next(
                (d for d in self.output_devices if d["id"] == device_id), None
            )
            if not output_device:
                self._append_status_threadsafe("Lỗi: Không thể lấy thông tin thiết bị")
                return

            sample_rate = int(output_device["sample_rate"])
            duration = 2.0  # 播放时长
            frequency = 440  # 440Hz A音

            self._append_status_threadsafe(
                f"开始播放测试 (设备: {device_id}, 采样率: {sample_rate}Hz)"
            )
            self._append_status_threadsafe("Vui lòng chuẩn bị tai nghe/loa, sắp phát âm kiểm tra...")

            # 倒计时提示
            for i in range(3, 0, -1):
                self._append_status_threadsafe(f"Bắt đầu phát sau {i} giây...")
                time.sleep(1)

            self._append_status_threadsafe(
                f"Đang phát âm kiểm tra {frequency}Hz ({duration}giây)..."
            )

            # 生成测试音频 (正弦波)
            t = np.linspace(0, duration, int(sample_rate * duration))
            # 添加淡入淡出效果，避免爆音
            fade_samples = int(0.1 * sample_rate)  # 0.1秒淡入淡出
            audio = 0.3 * np.sin(2 * np.pi * frequency * t)

            # 应用淡入淡出
            audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
            audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)

            # 播放音频
            sd.play(audio, samplerate=sample_rate, device=device_id)
            sd.wait()

            self._append_status_threadsafe("Phát hoàn tất")
            self._append_status_threadsafe(
                "Hướng dẫn kiểm tra: Nếu nghe thấy âm kiểm tra rõ ràng, loa/tai nghe hoạt động bình thường"
            )
            self._append_status_threadsafe(
                "Nếu không nghe thấy âm thanh, vui lòng kiểm tra cài đặt âm lượng hoặc chọn thiết bị đầu ra khác"
            )

        except Exception as e:
            self.logger.error(f"播放测试失败: {e}", exc_info=True)
            self._append_status_threadsafe(f"[Lỗi] Kiểm tra phát thất bại: {str(e)}")
        finally:
            # 重置UI状态（切回主线程）
            self._reset_output_ui_threadsafe()

    def _reset_input_test_ui(self):
        """
        Đặt lại trạng thái UI kiểm tra đầu vào.
        """
        self.testing_input = False
        self.ui_controls["test_input_btn"].setEnabled(True)
        self.ui_controls["test_input_btn"].setText("Kiểm tra")

    def _reset_input_ui_threadsafe(self):
        try:
            self.reset_input_ui.emit()
        except Exception as e:
            self.logger.error(f"Đặt lại UI kiểm tra đầu vào an toàn luồng thất bại: {e}")

    def _reset_output_test_ui(self):
        """
        Đặt lại trạng thái UI kiểm tra đầu ra.
        """
        self.testing_output = False
        self.ui_controls["test_output_btn"].setEnabled(True)
        self.ui_controls["test_output_btn"].setText("Kiểm tra")

    def _reset_output_ui_threadsafe(self):
        try:
            self.reset_output_ui.emit()
        except Exception as e:
            self.logger.error(f"Đặt lại UI kiểm tra đầu ra an toàn luồng thất bại: {e}")

    def _append_status(self, message):
        """
        Thêm thông tin trạng thái.
        """
        try:
            if self.ui_controls["status_text"]:
                current_time = time.strftime("%H:%M:%S")
                formatted_message = f"[{current_time}] {message}"
                self.ui_controls["status_text"].append(formatted_message)
                # 滚动到底部
                self.ui_controls["status_text"].verticalScrollBar().setValue(
                    self.ui_controls["status_text"].verticalScrollBar().maximum()
                )
        except Exception as e:
            self.logger.error(f"Thêm thông tin trạng thái thất bại: {e}", exc_info=True)

    def _append_status_threadsafe(self, message):
        """
        Thêm văn bản trạng thái vào QTextEdit một cách an toàn theo luồng nền (chuyển về luồng chính thông qua tín hiệu).
        """
        try:
            if not self.ui_controls.get("status_text"):
                return
            current_time = time.strftime("%H:%M:%S")
            formatted_message = f"[{current_time}] {message}"
            self.status_message.emit(formatted_message)
        except Exception as e:
            self.logger.error(f"Thêm trạng thái an toàn luồng thất bại: {e}", exc_info=True)

    def _on_status_message(self, formatted_message: str):
        try:
            if not self.ui_controls.get("status_text"):
                return
            self.ui_controls["status_text"].append(formatted_message)
            # 滚动到底部
            self.ui_controls["status_text"].verticalScrollBar().setValue(
                self.ui_controls["status_text"].verticalScrollBar().maximum()
            )
        except Exception as e:
            self.logger.error(f"Thêm văn bản trạng thái thất bại: {e}")

    def _load_config_values(self):
        """
        Tải giá trị từ tệp cấu hình vào điều khiển UI.
        """
        try:
            # 获取音频设备配置
            audio_config = self.config_manager.get_config("AUDIO_DEVICES", {})

            # 设置输入设备
            input_device_id = audio_config.get("input_device_id")
            if input_device_id is not None:
                index = self.ui_controls["input_device_combo"].findData(input_device_id)
                if index >= 0:
                    self.ui_controls["input_device_combo"].setCurrentIndex(index)

            # 设置输出设备
            output_device_id = audio_config.get("output_device_id")
            if output_device_id is not None:
                index = self.ui_controls["output_device_combo"].findData(
                    output_device_id
                )
                if index >= 0:
                    self.ui_controls["output_device_combo"].setCurrentIndex(index)

            # 设备信息在设备选择变更时自动更新，无需手动设置

        except Exception as e:
            self.logger.error(f"Tải giá trị cấu hình thiết bị âm thanh thất bại: {e}", exc_info=True)

    def get_config_data(self) -> dict:
        """
        Lấy dữ liệu cấu hình hiện tại.
        """
        config_data = {}

        try:
            audio_config = {}

            # 输入设备配置
            input_device_id = self.ui_controls["input_device_combo"].currentData()
            if input_device_id is not None:
                audio_config["input_device_id"] = input_device_id
                audio_config["input_device_name"] = self.ui_controls[
                    "input_device_combo"
                ].currentText()

            # 输出设备配置
            output_device_id = self.ui_controls["output_device_combo"].currentData()
            if output_device_id is not None:
                audio_config["output_device_id"] = output_device_id
                audio_config["output_device_name"] = self.ui_controls[
                    "output_device_combo"
                ].currentText()

            # 设备的采样率和声道信息由设备自动确定，不需要用户配置
            # 保存设备的默认采样率和声道用于后续使用
            input_device = next(
                (d for d in self.input_devices if d["id"] == input_device_id), None
            )
            if input_device:
                audio_config["input_sample_rate"] = int(input_device["sample_rate"])
                audio_config["input_channels"] = min(input_device["channels"], 8)

            output_device = next(
                (d for d in self.output_devices if d["id"] == output_device_id), None
            )
            if output_device:
                audio_config["output_sample_rate"] = int(output_device["sample_rate"])
                audio_config["output_channels"] = min(output_device["channels"], 8)

            if audio_config:
                config_data["AUDIO_DEVICES"] = audio_config

        except Exception as e:
            self.logger.error(f"Lấy dữ liệu cấu hình thiết bị âm thanh thất bại: {e}", exc_info=True)

        return config_data

    def reset_to_defaults(self):
        """
        Đặt lại về mặc định.
        """
        try:
            # 重新扫描设备
            self._scan_devices()

            # 设备扫描后采样率信息会自动显示，无需手动设置

            # 清空状态显示
            if self.ui_controls["status_text"]:
                self.ui_controls["status_text"].clear()

            self._append_status("Đã đặt lại về cài đặt mặc định")
            self.logger.info("Cấu hình thiết bị âm thanh đã được đặt lại về mặc định")

        except Exception as e:
            self.logger.error(f"Đặt lại cấu hình thiết bị âm thanh thất bại: {e}", exc_info=True)
