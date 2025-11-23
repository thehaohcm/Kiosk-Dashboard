# -*- coding: utf-8 -*-
"""
Mô hình dữ liệu cửa sổ hiển thị GUI - Dùng cho liên kết dữ liệu QML.
"""

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSignal


class GuiDisplayModel(QObject):
    """
    Mô hình dữ liệu cho cửa sổ chính GUI, dùng cho liên kết dữ liệu giữa Python và QML.
    """

    # 属性变化信号
    statusTextChanged = pyqtSignal()
    emotionPathChanged = pyqtSignal()
    ttsTextChanged = pyqtSignal()
    buttonTextChanged = pyqtSignal()
    modeTextChanged = pyqtSignal()
    autoModeChanged = pyqtSignal()

    # 用户操作信号
    manualButtonPressed = pyqtSignal()
    manualButtonReleased = pyqtSignal()
    autoButtonClicked = pyqtSignal()
    abortButtonClicked = pyqtSignal()
    modeButtonClicked = pyqtSignal()
    sendButtonClicked = pyqtSignal(str)  # 携带输入的文本
    settingsButtonClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # 私有属性
        self._status_text = "Trạng thái: Chưa kết nối"
        self._emotion_path = ""  # 表情资源路径（GIF/图片）或 emoji 字符
        self._tts_text = "Sẵn sàng"
        self._button_text = "Bắt đầu hội thoại"  # Văn bản nút chế độ tự động
        self._mode_text = "Hội thoại thủ công"  # Văn bản nút chuyển đổi chế độ
        self._auto_mode = False  # 是否自动模式
        self._is_connected = False

    # 状态文本属性
    @pyqtProperty(str, notify=statusTextChanged)
    def statusText(self):
        return self._status_text

    @statusText.setter
    def statusText(self, value):
        if self._status_text != value:
            self._status_text = value
            self.statusTextChanged.emit()

    # 表情路径属性
    @pyqtProperty(str, notify=emotionPathChanged)
    def emotionPath(self):
        return self._emotion_path

    @emotionPath.setter
    def emotionPath(self, value):
        if self._emotion_path != value:
            self._emotion_path = value
            self.emotionPathChanged.emit()

    # TTS 文本属性
    @pyqtProperty(str, notify=ttsTextChanged)
    def ttsText(self):
        return self._tts_text

    @ttsText.setter
    def ttsText(self, value):
        if self._tts_text != value:
            self._tts_text = value
            self.ttsTextChanged.emit()

    # 自动模式按钮文本属性
    @pyqtProperty(str, notify=buttonTextChanged)
    def buttonText(self):
        return self._button_text

    @buttonText.setter
    def buttonText(self, value):
        if self._button_text != value:
            self._button_text = value
            self.buttonTextChanged.emit()

    # 模式切换按钮文本属性
    @pyqtProperty(str, notify=modeTextChanged)
    def modeText(self):
        return self._mode_text

    @modeText.setter
    def modeText(self, value):
        if self._mode_text != value:
            self._mode_text = value
            self.modeTextChanged.emit()

    # 自动模式标志属性
    @pyqtProperty(bool, notify=autoModeChanged)
    def autoMode(self):
        return self._auto_mode

    @autoMode.setter
    def autoMode(self, value):
        if self._auto_mode != value:
            self._auto_mode = value
            self.autoModeChanged.emit()

    # 便捷方法
    def update_status(self, status: str, connected: bool):
        """
        Cập nhật văn bản trạng thái và trạng thái kết nối.
        """
        self.statusText = f"Trạng thái: {status}"
        self._is_connected = connected

    def update_text(self, text: str):
        """
        Cập nhật văn bản TTS.
        """
        self.ttsText = text

    def update_emotion(self, emotion_path: str):
        """
        Cập nhật đường dẫn biểu cảm.
        """
        self.emotionPath = emotion_path

    def update_button_text(self, text: str):
        """
        Cập nhật văn bản nút chế độ tự động.
        """
        self.buttonText = text

    def update_mode_text(self, text: str):
        """
        Cập nhật văn bản nút chế độ.
        """
        self.modeText = text

    def set_auto_mode(self, is_auto: bool):
        """
        Thiết lập chế độ tự động.
        """
        self.autoMode = is_auto
        if is_auto:
            self.modeText = "Hội thoại tự động"
        else:
            self.modeText = "Hội thoại thủ công"
