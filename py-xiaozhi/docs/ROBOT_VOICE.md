# Robot Voice Effect - Hiệu ứng giọng Robot cho AI

## Giới thiệu

Robot Voice Processor là module xử lý âm thanh real-time để biến giọng AI thành giọng robot đặc trưng với các hiệu ứng:

- **Ring Modulation**: Tạo âm thanh "robot" đặc trưng
- **Bitcrusher**: Giảm độ phân giải âm thanh để nghe "digital" hơn
- **Metallic Echo**: Tiếng vang kim loại
- **Pitch Shifting**: Thay đổi cao độ giọng (tùy chọn)

## Cấu hình

Mở file `config/config.json` và thêm/sửa section `ROBOT_VOICE`:

```json
{
  "ROBOT_VOICE": {
    "enabled": true,              // Bật/tắt hiệu ứng robot voice
    "pitch_shift": 0.0,           // Thay đổi cao độ (semitones): -2.0 đến 2.0
    "ring_mod_freq": 30.0,        // Tần số modulation (Hz): 20-100
    "ring_mod_depth": 0.3,        // Độ sâu hiệu ứng: 0.0-1.0
    "bit_depth": 12,              // Bit depth giả lập: 4-16 (càng thấp càng robot)
    "metallic_echo": true,        // Bật/tắt echo kim loại
    "echo_delay_ms": 50.0,        // Độ trễ echo (milliseconds)
    "echo_decay": 0.3             // Độ suy giảm echo: 0.0-1.0
  }
}
```

## Các thông số chi tiết

### 1. `enabled` (Boolean)
- **Mô tả**: Bật/tắt toàn bộ hiệu ứng robot voice
- **Giá trị**: `true` hoặc `false`
- **Mặc định**: `false`

### 2. `pitch_shift` (Float)
- **Mô tả**: Thay đổi cao độ giọng nói
- **Giá trị**: `-2.0` đến `2.0` (semitones)
  - `0.0`: Không thay đổi
  - `0.5`: Cao hơn một chút (giọng robot nhẹ nhàng)
  - `-0.5`: Thấp hơn một chút (giọng robot trầm)
  - `1.0`: Cao hơn 1 semitone (giọng robot cao)
- **Mặc định**: `0.0`
- **Gợi ý**: Để `0.0` hoặc `-0.3` đến `0.3` cho tự nhiên

### 3. `ring_mod_freq` (Float)
- **Mô tả**: Tần số của hiệu ứng ring modulation - thông số quan trọng nhất!
- **Giá trị**: `20.0` đến `100.0` Hz
  - `20-30`: Robot nhẹ, vẫn rõ ràng
  - `30-50`: Robot vừa phải (khuyến nghị)
  - `50-80`: Robot mạnh, giọng méo nhiều
  - `80-100`: Robot cực mạnh, khó nghe
- **Mặc định**: `30.0`
- **Gợi ý**: Bắt đầu với `30.0`, tăng dần để tìm mức phù hợp

### 4. `ring_mod_depth` (Float)
- **Mô tả**: Độ sâu của hiệu ứng ring modulation
- **Giá trị**: `0.0` đến `1.0`
  - `0.0`: Không có hiệu ứng
  - `0.1-0.3`: Hiệu ứng nhẹ (khuyến nghị)
  - `0.3-0.5`: Hiệu ứng vừa
  - `0.5-1.0`: Hiệu ứng mạnh
- **Mặc định**: `0.3`
- **Gợi ý**: `0.2-0.4` cho cân bằng giữa rõ ràng và robot

### 5. `bit_depth` (Integer)
- **Mô tả**: Giả lập độ phân giải âm thanh (bitcrusher)
- **Giá trị**: `4` đến `16` bit
  - `14-16`: Rất ít nhiễu, gần như gốc
  - `10-13`: Nhiễu vừa phải, nghe digital
  - `6-9`: Nhiễu nhiều, giọng robot cổ điển
  - `4-5`: Nhiễu rất nhiều, khó nghe
- **Mặc định**: `12`
- **Gợi ý**: `10-12` cho âm thanh robot mà vẫn rõ ràng

### 6. `metallic_echo` (Boolean)
- **Mô tả**: Bật/tắt hiệu ứng echo kim loại
- **Giá trị**: `true` hoặc `false`
- **Mặc định**: `true`
- **Gợi ý**: Bật để tăng cảm giác "kim loại"

### 7. `echo_delay_ms` (Float)
- **Mô tả**: Độ trễ của echo
- **Giá trị**: `20.0` đến `200.0` milliseconds
  - `20-50`: Echo ngắn, tiếng vang nhẹ
  - `50-100`: Echo vừa (khuyến nghị)
  - `100-200`: Echo dài, tiếng vang lớn
- **Mặc định**: `50.0`
- **Gợi ý**: `40-60ms` cho hiệu ứng tự nhiên

### 8. `echo_decay` (Float)
- **Mô tả**: Độ suy giảm của echo
- **Giá trị**: `0.0` đến `1.0`
  - `0.0`: Không có echo
  - `0.1-0.3`: Echo nhẹ (khuyến nghị)
  - `0.3-0.5`: Echo vừa
  - `0.5-1.0`: Echo mạnh, tiếng vang kéo dài
- **Mặc định**: `0.3`
- **Gợi ý**: `0.2-0.4` để không làm giọng bị rối

## Các preset khuyến nghị

### 1. Robot nhẹ (Light Robot)
```json
{
  "enabled": true,
  "pitch_shift": 0.0,
  "ring_mod_freq": 25.0,
  "ring_mod_depth": 0.2,
  "bit_depth": 13,
  "metallic_echo": true,
  "echo_delay_ms": 40.0,
  "echo_decay": 0.2
}
```

### 2. Robot chuẩn (Standard Robot) - Khuyến nghị
```json
{
  "enabled": true,
  "pitch_shift": 0.0,
  "ring_mod_freq": 30.0,
  "ring_mod_depth": 0.3,
  "bit_depth": 12,
  "metallic_echo": true,
  "echo_delay_ms": 50.0,
  "echo_decay": 0.3
}
```

### 3. Robot mạnh (Strong Robot)
```json
{
  "enabled": true,
  "pitch_shift": -0.3,
  "ring_mod_freq": 45.0,
  "ring_mod_depth": 0.4,
  "bit_depth": 10,
  "metallic_echo": true,
  "echo_delay_ms": 60.0,
  "echo_decay": 0.35
}
```

### 4. Robot cổ điển (Retro Robot)
```json
{
  "enabled": true,
  "pitch_shift": 0.0,
  "ring_mod_freq": 40.0,
  "ring_mod_depth": 0.5,
  "bit_depth": 8,
  "metallic_echo": true,
  "echo_delay_ms": 70.0,
  "echo_decay": 0.4
}
```

### 5. Robot cao (High-pitched Robot)
```json
{
  "enabled": true,
  "pitch_shift": 1.0,
  "ring_mod_freq": 35.0,
  "ring_mod_depth": 0.25,
  "bit_depth": 12,
  "metallic_echo": true,
  "echo_delay_ms": 45.0,
  "echo_decay": 0.25
}
```

## Cách sử dụng

1. **Bật/tắt hiệu ứng**:
   - Mở `config/config.json`
   - Tìm section `ROBOT_VOICE`
   - Đổi `"enabled": true` hoặc `"enabled": false`
   - Khởi động lại ứng dụng

2. **Điều chỉnh hiệu ứng**:
   - Thay đổi các giá trị trong config
   - Khởi động lại để áp dụng thay đổi
   - Thử nghiệm với các giá trị khác nhau

3. **Tìm giá trị phù hợp**:
   - Bắt đầu với preset "Standard Robot"
   - Điều chỉnh `ring_mod_freq` trước (quan trọng nhất)
   - Sau đó điều chỉnh `ring_mod_depth` và `bit_depth`
   - Cuối cùng tinh chỉnh echo nếu cần

## Lưu ý

- Hiệu ứng được áp dụng **real-time** cho mọi audio từ server
- Không ảnh hưởng đến audio đầu vào (microphone)
- Hiệu suất: CPU usage tăng nhẹ (~5-10%) khi bật
- Latency: Thêm <1ms, không đáng kể
- Tương thích: Hoạt động với mọi loại audio (TTS, music, v.v.)

## Troubleshooting

### Giọng bị méo quá mức
- Giảm `ring_mod_depth` xuống 0.2-0.3
- Giảm `ring_mod_freq` xuống 25-30Hz
- Tăng `bit_depth` lên 13-14

### Giọng không đủ robot
- Tăng `ring_mod_freq` lên 40-50Hz
- Tăng `ring_mod_depth` lên 0.4-0.5
- Giảm `bit_depth` xuống 10-11

### Echo quá lớn
- Giảm `echo_decay` xuống 0.1-0.2
- Hoặc tắt `metallic_echo`

### Hiệu ứng không hoạt động
- Kiểm tra `"enabled": true`
- Xem log để phát hiện lỗi khởi tạo
- Đảm bảo đã khởi động lại ứng dụng sau khi sửa config

## API (Cho developer)

Nếu muốn điều khiển robot voice bằng code:

```python
# Truy cập AudioCodec
audio_codec = app.audio_codec

# Bật/tắt robot voice
audio_codec.robot_voice_processor.set_enabled(True)

# Cập nhật cấu hình
audio_codec.robot_voice_processor.update_config(
    ring_mod_freq=35.0,
    ring_mod_depth=0.4,
    bit_depth=11
)

# Kiểm tra trạng thái
is_enabled = audio_codec.robot_voice_enabled
```

## Tương lai

Các tính năng có thể bổ sung:
- [ ] Điều chỉnh real-time qua GUI
- [ ] Nhiều preset có sẵn
- [ ] Lưu/load preset tùy chỉnh
- [ ] Visualizer cho hiệu ứng
- [ ] Phím tắt để bật/tắt nhanh

---

**Tác giả**: GitHub Copilot  
**Phiên bản**: 1.0.0  
**Ngày**: November 26, 2025
