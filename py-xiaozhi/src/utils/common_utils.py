"""
Mô-đun tổng hợp các hàm tiện ích chung bao gồm chuyển văn bản thành giọng nói, thao tác trình duyệt, khay nhớ tạm và các hàm tiện ích chung khác.
"""

import queue
import shutil
import threading
import time
import webbrowser
from typing import Optional

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# 全局音频播放队列和锁
_audio_queue = queue.Queue()
_audio_lock = threading.Lock()
_audio_worker_thread = None
_audio_worker_running = False
_audio_device_warmed_up = False


def _warm_up_audio_device():
    """
    Làm nóng thiết bị âm thanh để ngăn chữ đầu tiên bị nuốt mất.
    """
    global _audio_device_warmed_up
    if _audio_device_warmed_up:
        return

    try:
        import platform
        import subprocess

        system = platform.system()

        if system == "Darwin":
            subprocess.run(
                ["say", "-v", "Ting-Ting", "ưm"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif system == "Linux" and shutil.which("espeak"):
            subprocess.run(
                ["espeak", "-v", "vi", "ưm"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif system == "Windows":
            import win32com.client

            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            speaker.Speak("ưm")

        _audio_device_warmed_up = True
        logger.info("Đã làm nóng thiết bị âm thanh")
    except Exception as e:
        logger.warning(f"Làm nóng thiết bị âm thanh thất bại: {e}")


def _audio_queue_worker():
    """
    Luồng làm việc hàng đợi âm thanh, đảm bảo âm thanh được phát theo thứ tự và không bị cắt ngang.
    """

    while _audio_worker_running:
        try:
            text = _audio_queue.get(timeout=1)
            if text is None:
                break

            with _audio_lock:
                logger.info(f"Bắt đầu phát âm thanh: {text[:50]}...")
                success = _play_system_tts(text)

                if not success:
                    logger.warning("TTS hệ thống thất bại, thử phương án dự phòng")
                    import os

                    if os.name == "nt":
                        _play_windows_tts(text, set_vietnamese_voice=False)
                    else:
                        _play_system_tts(text)

                time.sleep(0.5)  # Tạm dừng sau khi phát xong để ngăn âm cuối bị nuốt mất

            _audio_queue.task_done()

        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Lỗi luồng làm việc hàng đợi âm thanh: {e}")

    logger.info("Luồng làm việc hàng đợi âm thanh đã dừng")


def _ensure_audio_worker():
    """
    Đảm bảo luồng làm việc âm thanh đang chạy.
    """
    global _audio_worker_thread, _audio_worker_running

    if _audio_worker_thread is None or not _audio_worker_thread.is_alive():
        _warm_up_audio_device()
        _audio_worker_running = True
        _audio_worker_thread = threading.Thread(target=_audio_queue_worker, daemon=True)
        _audio_worker_thread.start()
        logger.info("Luồng làm việc hàng đợi âm thanh đã được khởi động")


def open_url(url: str) -> bool:
    try:
        success = webbrowser.open(url)
        if success:
            logger.info(f"Đã mở thành công trang web: {url}")
        else:
            logger.warning(f"Không thể mở trang web: {url}")
        return success
    except Exception as e:
        logger.error(f"Lỗi khi mở trang web: {e}")
        return False


def copy_to_clipboard(text: str) -> bool:
    try:
        import pyperclip

        pyperclip.copy(text)
        logger.info(f'Văn bản "{text}" đã được sao chép vào khay nhớ tạm')
        return True
    except ImportError:
        logger.warning("Chưa cài đặt mô-đun pyperclip, không thể sao chép vào khay nhớ tạm")
        return False
    except Exception as e:
        logger.error(f"Lỗi khi sao chép vào khay nhớ tạm: {e}")
        return False


def _play_windows_tts(text: str, set_chinese_voice: bool = True) -> bool:
    try:
        import win32com.client

        speaker = win32com.client.Dispatch("SAPI.SpVoice")

        if set_chinese_voice:
            try:
                voices = speaker.GetVoices()
                for i in range(voices.Count):
                    if "Vietnamese" in voices.Item(i).GetDescription():
                        speaker.Voice = voices.Item(i)
                        break
            except Exception as e:
                logger.warning(f"Lỗi khi thiết lập giọng nói tiếng Việt: {e}")

        try:
            speaker.Rate = -2
        except Exception:
            pass

        enhanced_text = text + "。 。 。"
        speaker.Speak(enhanced_text)
        logger.info("Đã phát văn bản bằng tổng hợp giọng nói Windows")
        time.sleep(0.5)
        return True
    except ImportError:
        logger.warning("Windows TTS不可用，跳过音频播放")
        return False
    except Exception as e:
        logger.error(f"Lỗi phát TTS Windows: {e}")
        return False


def _play_linux_tts(text: str) -> bool:
    import subprocess

    if shutil.which("espeak"):
        try:
            enhanced_text = text + ". . ."
            result = subprocess.run(
                ["espeak", "-v", "vi", "-s", "150", "-g", "10", enhanced_text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
            )
            time.sleep(0.5)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.warning("Hết thời gian phát espeak")
            return False
        except Exception as e:
            logger.error(f"Lỗi phát espeak: {e}")
            return False
    else:
        logger.warning("espeak không khả dụng, bỏ qua phát âm thanh")
        return False


def _play_macos_tts(text: str) -> bool:
    import subprocess

    if shutil.which("say"):
        try:
            enhanced_text = text + ". . ."
            result = subprocess.run(
                ["say", "-r", "180", enhanced_text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
            )
            time.sleep(0.5)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.warning("Hết thời gian lệnh say")
            return False
        except Exception as e:
            logger.error(f"Lỗi phát lệnh say: {e}")
            return False
    else:
        logger.warning("Lệnh say không khả dụng, bỏ qua phát âm thanh")
        return False


def _play_system_tts(text: str) -> bool:
    import os
    import platform

    if os.name == "nt":
        return _play_windows_tts(text)
    else:
        system = platform.system()
        if system == "Linux":
            return _play_linux_tts(text)
        elif system == "Darwin":
            return _play_macos_tts(text)
        else:
            logger.warning(f"Hệ thống không được hỗ trợ {system}, bỏ qua phát âm thanh")
            return False


def play_audio_nonblocking(text: str) -> None:
    try:
        _ensure_audio_worker()
        _audio_queue.put(text)
        logger.info(f"Đã thêm nhiệm vụ âm thanh vào hàng đợi: {text[:50]}...")
    except Exception as e:
        logger.error(f"Lỗi khi thêm nhiệm vụ âm thanh vào hàng đợi: {e}")

        def audio_worker():
            try:
                _warm_up_audio_device()
                _play_system_tts(text)
            except Exception as e:
                logger.error(f"Lỗi phát âm thanh dự phòng: {e}")

        threading.Thread(target=audio_worker, daemon=True).start()


def extract_verification_code(text: str) -> Optional[str]:
    try:
        import re

        # 激活相关关键词列表
        activation_keywords = [
            "Đăng nhập",
            "Bảng điều khiển",
            "Kích hoạt",
            "Mã xác minh",
            "Liên kết thiết bị",
            "Thêm thiết bị",
            "Nhập mã xác minh",
            "Nhập",
            "Bảng",
            "xiaozhi.me",
            "Mã kích hoạt",
        ]

        # 检查文本是否包含激活相关关键词
        has_activation_keyword = any(keyword in text for keyword in activation_keywords)

        if not has_activation_keyword:
            logger.debug(f"文本不包含激活关键词，跳过验证码提取: {text}")
            return None

        # 更精确的验证码匹配模式
        # 匹配6位数字的验证码，可能有空格分隔
        patterns = [
            r"mã xác minh[：:]\s*(\d{6})",  # mã xác minh：123456
            r"nhập mã xác minh[：:]\s*(\d{6})",  # nhập mã xác minh：123456
            r"nhập\s*(\d{6})",  # nhập123456
            r"mã xác minh\s*(\d{6})",  # mã xác minh123456
            r"mã kích hoạt[：:]\s*(\d{6})",  # mã kích hoạt：123456
            r"(\d{6})[，,。.]",  # 123456，或123456。
            r"[，,。.]\s*(\d{6})",  # ，123456
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                code = match.group(1)
                logger.info(f"已从文本中提取验证码: {code}")
                return code

        # 如果有激活关键词但没有匹配到精确模式，尝试原始模式
        # 但要求数字周围有特定的上下文
        match = re.search(r"((?:\d\s*){6,})", text)
        if match:
            code = "".join(match.group(1).split())
            # Mã xác minh nên là 6 chữ số
            if len(code) == 6 and code.isdigit():
                logger.info(f"Đã trích xuất mã xác minh từ văn bản (chế độ chung): {code}")
                return code

        logger.warning(f"Không thể tìm thấy mã xác minh trong văn bản: {text}")
        return None
    except Exception as e:
        logger.error(f"Lỗi khi trích xuất mã xác minh: {e}")
        return None


def handle_verification_code(text: str) -> None:
    code = extract_verification_code(text)
    if not code:
        return

    copy_to_clipboard(code)
