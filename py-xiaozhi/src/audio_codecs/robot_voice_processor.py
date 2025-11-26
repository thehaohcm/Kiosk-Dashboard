"""
Robot Voice Processor - Xử lý hiệu ứng giọng robot cho audio
"""
import numpy as np
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class RobotVoiceProcessor:
    """
    Xử lý audio để tạo hiệu ứng giọng robot.
    
    Các hiệu ứng:
    - Pitch shifting (thay đổi cao độ giọng)
    - Ring modulation (hiệu ứng robot)
    - Bitcrusher (giảm bit depth)
    - Metallic echo (tiếng vang kim loại)
    """
    
    def __init__(
        self,
        sample_rate: int = 24000,
        enabled: bool = True,
        pitch_shift_semitones: float = 0.0,  # Số semitone tăng/giảm (0.5 = cao hơn chút, -0.5 = thấp hơn chút)
        ring_mod_freq: float = 30.0,  # Tần số modulation (Hz) - càng cao càng robot
        ring_mod_depth: float = 0.3,  # Độ sâu hiệu ứng (0-1)
        bit_depth: int = 12,  # Bit depth giả lập (8-16, càng thấp càng robot)
        metallic_echo: bool = True,  # Bật/tắt echo kim loại
        echo_delay_ms: float = 50.0,  # Độ trễ echo (ms)
        echo_decay: float = 0.3,  # Độ suy giảm echo (0-1)
    ):
        self.sample_rate = sample_rate
        self.enabled = enabled
        
        # Cấu hình hiệu ứng
        self.pitch_shift_semitones = pitch_shift_semitones
        self.ring_mod_freq = ring_mod_freq
        self.ring_mod_depth = ring_mod_depth
        self.bit_depth = bit_depth
        self.metallic_echo = metallic_echo
        self.echo_delay_ms = echo_delay_ms
        self.echo_decay = echo_decay
        
        # Buffer cho echo
        self.echo_buffer_size = int(sample_rate * echo_delay_ms / 1000)
        self.echo_buffer = np.zeros(self.echo_buffer_size, dtype=np.float32)
        
        # Phase accumulator cho ring modulation
        self.ring_mod_phase = 0.0
        
        logger.info(
            f"RobotVoiceProcessor khởi tạo: "
            f"pitch={pitch_shift_semitones}, "
            f"ring_mod={ring_mod_freq}Hz, "
            f"bit_depth={bit_depth}, "
            f"echo={'on' if metallic_echo else 'off'}"
        )
    
    def process(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Xử lý audio với hiệu ứng robot.
        
        Args:
            audio_data: PCM audio data (int16)
            
        Returns:
            Processed audio data (int16)
        """
        if not self.enabled:
            return audio_data
        
        try:
            # Chuyển sang float32 để xử lý (-1.0 đến 1.0)
            audio_float = audio_data.astype(np.float32) / 32768.0
            
            # 1. Ring Modulation (hiệu ứng robot chính)
            audio_float = self._apply_ring_modulation(audio_float)
            
            # 2. Bitcrusher (giảm độ phân giải)
            audio_float = self._apply_bitcrusher(audio_float)
            
            # 3. Metallic Echo
            if self.metallic_echo:
                audio_float = self._apply_metallic_echo(audio_float)
            
            # 4. Pitch Shift (nếu có)
            if self.pitch_shift_semitones != 0.0:
                audio_float = self._apply_pitch_shift(audio_float)
            
            # Chuyển lại int16
            audio_int16 = (audio_float * 32768.0).clip(-32768, 32767).astype(np.int16)
            
            return audio_int16
            
        except Exception as e:
            logger.error(f"Lỗi xử lý robot voice: {e}")
            return audio_data
    
    def _apply_ring_modulation(self, audio: np.ndarray) -> np.ndarray:
        """
        Ring modulation - Nhân audio với sine wave tần số thấp.
        Tạo hiệu ứng "robot" đặc trưng.
        """
        num_samples = len(audio)
        
        # Tạo carrier wave
        phase_increment = 2.0 * np.pi * self.ring_mod_freq / self.sample_rate
        phases = self.ring_mod_phase + phase_increment * np.arange(num_samples)
        carrier = np.sin(phases)
        
        # Cập nhật phase cho lần sau
        self.ring_mod_phase = phases[-1] % (2.0 * np.pi)
        
        # Mix: audio gốc + (audio * carrier)
        modulated = audio * (1.0 - self.ring_mod_depth) + \
                    audio * carrier * self.ring_mod_depth
        
        return modulated
    
    def _apply_bitcrusher(self, audio: np.ndarray) -> np.ndarray:
        """
        Bitcrusher - Giảm bit depth để tạo âm thanh "digital" hơn.
        """
        # Tính số bước lượng tử hóa
        steps = 2 ** self.bit_depth
        
        # Lượng tử hóa
        quantized = np.round(audio * steps) / steps
        
        return quantized
    
    def _apply_metallic_echo(self, audio: np.ndarray) -> np.ndarray:
        """
        Metallic echo - Echo ngắn với tần số cao để tạo âm kim loại.
        """
        output = np.zeros_like(audio)
        
        for i in range(len(audio)):
            # Lấy echo từ buffer
            echo_sample = self.echo_buffer[0] if len(self.echo_buffer) > 0 else 0.0
            
            # Mix audio gốc với echo
            output[i] = audio[i] + echo_sample * self.echo_decay
            
            # Cập nhật buffer (FIFO)
            self.echo_buffer = np.roll(self.echo_buffer, -1)
            self.echo_buffer[-1] = output[i]
        
        return output
    
    def _apply_pitch_shift(self, audio: np.ndarray) -> np.ndarray:
        """
        Pitch shifting đơn giản bằng cách thay đổi tốc độ phát.
        (Phiên bản đơn giản, không giữ nguyên thời lượng)
        """
        try:
            # Tính tỷ lệ pitch (semitone -> ratio)
            ratio = 2.0 ** (self.pitch_shift_semitones / 12.0)
            
            # Resample với tỷ lệ mới
            new_length = int(len(audio) / ratio)
            indices = np.linspace(0, len(audio) - 1, new_length)
            
            # Linear interpolation
            shifted = np.interp(indices, np.arange(len(audio)), audio)
            
            # Pad hoặc trim về độ dài gốc
            if len(shifted) < len(audio):
                # Pad với zeros
                padded = np.zeros(len(audio), dtype=np.float32)
                padded[:len(shifted)] = shifted
                return padded
            else:
                # Trim
                return shifted[:len(audio)]
                
        except Exception as e:
            logger.warning(f"Pitch shift thất bại: {e}")
            return audio
    
    def set_enabled(self, enabled: bool):
        """Bật/tắt hiệu ứng robot voice."""
        self.enabled = enabled
        logger.info(f"Robot voice: {'BẬT' if enabled else 'TẮT'}")
    
    def update_config(
        self,
        pitch_shift_semitones: float = None,
        ring_mod_freq: float = None,
        ring_mod_depth: float = None,
        bit_depth: int = None,
        metallic_echo: bool = None,
        echo_delay_ms: float = None,
        echo_decay: float = None,
    ):
        """Cập nhật cấu hình hiệu ứng."""
        if pitch_shift_semitones is not None:
            self.pitch_shift_semitones = pitch_shift_semitones
        if ring_mod_freq is not None:
            self.ring_mod_freq = ring_mod_freq
        if ring_mod_depth is not None:
            self.ring_mod_depth = ring_mod_depth
        if bit_depth is not None:
            self.bit_depth = max(4, min(16, bit_depth))  # Giới hạn 4-16 bit
        if metallic_echo is not None:
            self.metallic_echo = metallic_echo
        if echo_delay_ms is not None:
            self.echo_delay_ms = echo_delay_ms
            # Cập nhật buffer size
            new_size = int(self.sample_rate * echo_delay_ms / 1000)
            if new_size != self.echo_buffer_size:
                self.echo_buffer_size = new_size
                self.echo_buffer = np.zeros(self.echo_buffer_size, dtype=np.float32)
        if echo_decay is not None:
            self.echo_decay = echo_decay
        
        logger.info(f"Robot voice config cập nhật: ring_mod={self.ring_mod_freq}Hz, bit={self.bit_depth}")
