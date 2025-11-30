from typing import Any, Optional

from src.constants.constants import AbortReason, DeviceState
from src.plugins.base import Plugin
from src.utils.logging_config import get_logger


class UIPlugin(Plugin):
    """UI 插件 - 管理 CLI/GUI 显示"""

    name = "ui"
    priority = 60  # UI 需要在其他插件完成后初始化

    # 设备状态文本映射
    STATE_TEXT_MAP = {
        DeviceState.IDLE: "Sẵn sàng",
        DeviceState.LISTENING: "Đang lắng nghe...",
        DeviceState.SPEAKING: "Đang nói...",
    }

    def __init__(self, mode: Optional[str] = None) -> None:
        super().__init__()
        self.logger = get_logger(__name__)
        self.app = None
        self.mode = (mode or "cli").lower()
        self.display = None
        self._is_gui = False
        self.is_first = True

    async def setup(self, app: Any) -> None:
        """
        初始化 UI 插件.
        """
        self.app = app

        # 创建对应的 display 实例
        self.display = self._create_display()

        # 禁用应用内控制台输入
        if hasattr(app, "use_console_input"):
            app.use_console_input = False

    def _create_display(self):
        """
        根据模式创建 display 实例.
        """
        if self.mode == "gui":
            from src.display.gui_display import GuiDisplay

            self._is_gui = True
            return GuiDisplay()
        else:
            from src.display.cli_display import CliDisplay

            self._is_gui = False
            return CliDisplay()

    async def start(self) -> None:
        """
        启动 UI 显示.
        """
        if not self.display:
            return

        # 绑定回调
        await self._setup_callbacks()

        # 启动显示
        self.app.spawn(self.display.start(), name=f"ui:{self.mode}:start")

    async def _setup_callbacks(self) -> None:
        """
        设置 display 回调.
        """
        if self._is_gui:
            # GUI 需要调度到异步任务
            callbacks = {
                "press_callback": self._wrap_callback(self._press),
                "release_callback": self._wrap_callback(self._release),
                "auto_callback": self._wrap_callback(self._auto_toggle),
                "abort_callback": self._wrap_callback(self._abort),
                "send_text_callback": self._send_text,
            }
        else:
            # CLI 直接传递协程函数
            callbacks = {
                "auto_callback": self._auto_toggle,
                "abort_callback": self._abort,
                "send_text_callback": self._send_text,
            }

        await self.display.set_callbacks(**callbacks)

    def _wrap_callback(self, coro_func):
        """
        包装协程函数为可调度的 lambda.
        """
        return lambda: self.app.spawn(coro_func(), name="ui:callback")

    async def on_incoming_json(self, message: Any) -> None:
        """
        处理传入的 JSON 消息.
        """
        if not self.display or not isinstance(message, dict):
            return

        msg_type = message.get("type")
        
        # Log để debug
        if msg_type in ("tts", "stt", "llm"):
            self.logger.info(f"📨 Nhận được response từ AI: type={msg_type}, text={message.get('text', '')[:50]}")

        # tts/stt 都更新文本
        if msg_type in ("tts", "stt"):
            if text := message.get("text"):
                await self.display.update_text(text)
                self.logger.info(f"✅ Đã cập nhật UI với AI response")

        # llm 更新表情
        elif msg_type == "llm":
            if emotion := message.get("emotion"):
                await self.display.update_emotion(emotion)
                self.logger.info(f"✅ Đã cập nhật emotion: {emotion}")

    async def on_device_state_changed(self, state: Any) -> None:
        """
        设备状态变化处理.
        """
        if not self.display:
            return

        # 跳过首次调用
        if self.is_first:
            self.is_first = False
            return

        # 更新表情和状态
        await self.display.update_emotion("neutral")
        if status_text := self.STATE_TEXT_MAP.get(state):
            await self.display.update_status(status_text, True)

    async def shutdown(self) -> None:
        """
        清理 UI 资源，关闭窗口.
        """
        if self.display:
            await self.display.close()
            self.display = None

    # ===== 回调函数 =====

    async def _send_text(self, text: str):
        """
        发送文本到服务端.
        """
        self.logger.info(f"🚀 _send_text được gọi với text: '{text[:50]}...' (độ dài: {len(text)})")
        self.logger.info(f"Device state hiện tại: {self.app.device_state}")
        
        # Cập nhật UI ngay lập tức
        try:
            self.logger.info("Đang cập nhật UI với text người dùng...")
            await self.display.update_text(f"Bạn: {text}")
            self.logger.info("✅ Đã cập nhật text UI")
            await self.display.update_status("Đang gửi câu hỏi...", True)
            self.logger.info("✅ Đã cập nhật status UI")
        except Exception as e:
            self.logger.error(f"❌ Lỗi khi cập nhật UI: {e}", exc_info=True)
        
        if self.app.device_state == DeviceState.SPEAKING:
            self.logger.info("Đang SPEAKING, abort audio trước...")
            audio_plugin = self.app.plugins.get_plugin("audio")
            if audio_plugin:
                await audio_plugin.codec.clear_audio_queue()
            await self.app.abort_speaking(None)
            
        self.logger.info("Đang connect protocol...")
        if await self.app.connect_protocol():
            self.logger.info(f"✅ Protocol connected, gửi text: '{text[:30]}...'")
            try:
                await self.app.protocol.send_wake_word_detected(text)
                self.logger.info("✅ Text đã được gửi thành công!")
                # Cập nhật UI sau khi gửi
                try:
                    await self.display.update_status("Đang chờ phản hồi từ AI...", True)
                    self.logger.info("✅ Đã cập nhật status: Đang chờ AI")
                    
                    # Tạo timeout task để kiểm tra sau 30s
                    import asyncio
                    self.app.spawn(self._check_response_timeout(text), "ui:response_timeout")
                    
                except Exception as e:
                    self.logger.error(f"❌ Lỗi cập nhật status sau gửi: {e}", exc_info=True)
            except Exception as e:
                self.logger.error(f"❌ Lỗi khi gửi text: {e}", exc_info=True)
                await self.display.update_status("Lỗi khi gửi câu hỏi", False)
        else:
            self.logger.error("❌ Không thể connect protocol!")
            await self.display.update_status("Không thể kết nối", False)
    
    async def _check_response_timeout(self, original_text: str):
        """
        Kiểm tra timeout 30s cho response từ server.
        """
        import asyncio
        
        # Lưu device state hiện tại
        initial_state = self.app.device_state
        
        # Đợi 30 giây
        await asyncio.sleep(30)
        
        # Kiểm tra nếu vẫn đang listening (chưa nhận được response)
        if self.app.device_state == DeviceState.LISTENING:
            self.logger.warning(f"⏰ Timeout 30s - Server không response cho câu hỏi: '{original_text[:50]}...'")
            
            # Hiển thị thông báo lỗi
            error_message = "Server hiện đang quá tải, bạn thử lại sau nhé"
            
            try:
                # Cập nhật UI
                await self.display.update_emotion("sad")
                await self.display.update_text(f"AI: {error_message}")
                await self.display.update_status("Server quá tải", False)
                
                # Phát âm thanh TTS nếu có
                try:
                    if await self.app.connect_protocol():
                        # Tạo fake response để trigger TTS
                        fake_response = {
                            "type": "tts",
                            "text": error_message
                        }
                        await self.app.plugins.notify_incoming_json(fake_response)
                        self.logger.info("✅ Đã phát thông báo timeout qua TTS")
                except Exception as e:
                    self.logger.error(f"Không thể phát TTS timeout: {e}")
                
                # Reset về IDLE sau 2 giây
                await asyncio.sleep(2)
                await self.app.set_device_state(DeviceState.IDLE)
                await self.display.update_status("Sẵn sàng", True)
                
            except Exception as e:
                self.logger.error(f"❌ Lỗi khi xử lý timeout: {e}", exc_info=True)
        else:
            self.logger.info(f"✅ Server đã response trước khi timeout (state: {self.app.device_state})")

    async def _press(self):
        """
        手动模式：按下开始录音.
        """
        await self.app.start_listening_manual()

    async def _release(self):
        """
        手动模式：释放停止录音.
        """
        await self.app.stop_listening_manual()

    async def _auto_toggle(self):
        """
        自动模式切换.
        """
        await self.app.start_auto_conversation()

    async def _abort(self):
        """
        中断对话.
        """
        await self.app.abort_speaking(AbortReason.USER_INTERRUPTION)
