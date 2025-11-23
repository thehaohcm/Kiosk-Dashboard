import json
import uuid
from typing import Any, Dict

from src.utils.logging_config import get_logger
from src.utils.resource_finder import resource_finder

logger = get_logger(__name__)


class ConfigManager:
    """Trình quản lý cấu hình - Chế độ đơn lẻ"""

    _instance = None

    # Cấu hình mặc định
    DEFAULT_CONFIG = {
        "SYSTEM_OPTIONS": {
            "CLIENT_ID": None,
            "DEVICE_ID": None,
            "NETWORK": {
                "OTA_VERSION_URL": "https://api.tenclass.net/xiaozhi/ota/",
                "WEBSOCKET_URL": None,
                "WEBSOCKET_ACCESS_TOKEN": None,
                "MQTT_INFO": None,
                "ACTIVATION_VERSION": "v2",  # Các giá trị tùy chọn: v1, v2
                "AUTHORIZATION_URL": "https://xiaozhi.me/",
            },
        },
        "WAKE_WORD_OPTIONS": {
            "USE_WAKE_WORD": True,
            "MODEL_PATH": "models",
            "NUM_THREADS": 4,
            "PROVIDER": "cpu",
            "MAX_ACTIVE_PATHS": 2,
            "KEYWORDS_SCORE": 1.8,
            "KEYWORDS_THRESHOLD": 0.2,
            "NUM_TRAILING_BLANKS": 1,
        },
        "CAMERA": {
            "camera_index": 0,
            "frame_width": 640,
            "frame_height": 480,
            "fps": 30,
            "Local_VL_url": "https://open.bigmodel.cn/api/paas/v4/",
            "VLapi_key": "",
            "models": "glm-4v-plus",
        },
        "SHORTCUTS": {
            "ENABLED": True,
            "MANUAL_PRESS": {"modifier": "ctrl", "key": "j", "description": "按住说话"},
            "AUTO_TOGGLE": {"modifier": "ctrl", "key": "k", "description": "自动对话"},
            "ABORT": {"modifier": "ctrl", "key": "q", "description": "中断对话"},
            "MODE_TOGGLE": {"modifier": "ctrl", "key": "m", "description": "切换模式"},
            "WINDOW_TOGGLE": {
                "modifier": "ctrl",
                "key": "w",
                "description": "显示/隐藏窗口",
            },
        },
        "AEC_OPTIONS": {
            "ENABLED": False,
            "BUFFER_MAX_LENGTH": 200,
            "FRAME_DELAY": 3,
            "FILTER_LENGTH_RATIO": 0.4,
            "ENABLE_PREPROCESS": True,
        },
        "AUDIO_DEVICES": {
            "input_device_id": None,
            "input_device_name": None,
            "output_device_id": None,
            "output_device_name": None,
            "input_sample_rate": None,
            "output_sample_rate": None,
            "input_channels": None,
            "output_channels": None,
        },
    }

    def __new__(cls):
        """
        Đảm bảo chế độ đơn lẻ.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        Khởi tạo trình quản lý cấu hình.
        """
        if self._initialized:
            return
        self._initialized = True

        # 初始化配置文件路径
        self._init_config_paths()

        # 确保必要的目录存在
        self._ensure_required_directories()

        # 加载配置
        self._config = self._load_config()

    def _init_config_paths(self):
        """
        Khởi tạo đường dẫn tệp cấu hình.
        """
        # 使用resource_finder查找或创建配置目录
        self.config_dir = resource_finder.find_config_dir()
        if not self.config_dir:
            # 如果找不到配置目录，在项目根目录下创建
            project_root = resource_finder.get_project_root()
            self.config_dir = project_root / "config"
            self.config_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Tạo thư mục cấu hình: {self.config_dir.absolute()}")

        self.config_file = self.config_dir / "config.json"

        # 记录配置文件路径
        logger.info(f"配置目录: {self.config_dir.absolute()}")
        logger.info(f"配置文件: {self.config_file.absolute()}")

    def _ensure_required_directories(self):
        """
        Đảm bảo các thư mục cần thiết tồn tại.
        """
        project_root = resource_finder.get_project_root()

        # 创建 models 目录
        models_dir = project_root / "models"
        if not models_dir.exists():
            models_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Tạo thư mục mô hình: {models_dir.absolute()}")

        # 创建 cache 目录
        cache_dir = project_root / "cache"
        if not cache_dir.exists():
            cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Tạo thư mục đệm: {cache_dir.absolute()}")

    def _load_config(self) -> Dict[str, Any]:
        """
        Tải tệp cấu hình, nếu không tồn tại thì tạo mới.
        """
        try:
            # 首先尝试使用resource_finder查找配置文件
            config_file_path = resource_finder.find_file("config/config.json")

            if config_file_path:
                logger.debug(f"Sử dụng resource_finder tìm thấy tệp cấu hình: {config_file_path}")
                config = json.loads(config_file_path.read_text(encoding="utf-8"))
                return self._merge_configs(self.DEFAULT_CONFIG, config)

            # 如果resource_finder没找到，尝试使用实例变量中的路径
            if self.config_file.exists():
                logger.debug(f"Sử dụng đường dẫn thể hiện tìm thấy tệp cấu hình: {self.config_file}")
                config = json.loads(self.config_file.read_text(encoding="utf-8"))
                return self._merge_configs(self.DEFAULT_CONFIG, config)
            else:
                # 创建默认配置文件
                logger.info("Tệp cấu hình không tồn tại, tạo cấu hình mặc định")
                self._save_config(self.DEFAULT_CONFIG)
                return self.DEFAULT_CONFIG.copy()

        except Exception as e:
            logger.error(f"Lỗi tải cấu hình: {e}")
            return self.DEFAULT_CONFIG.copy()

    def _save_config(self, config: dict) -> bool:
        """
        Lưu cấu hình vào tệp.
        """
        try:
            # 确保配置目录存在
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # 保存配置文件
            self.config_file.write_text(
                json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            logger.debug(f"Cấu hình đã được lưu vào: {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"Lỗi lưu cấu hình: {e}")
            return False

    @staticmethod
    def _merge_configs(default: dict, custom: dict) -> dict:
        """
        Hợp nhất đệ quy từ điển cấu hình.
        """
        result = default.copy()
        for key, value in custom.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = ConfigManager._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    def get_config(self, path: str, default: Any = None) -> Any:
        """
        Lấy giá trị cấu hình qua đường dẫn
        path: Đường dẫn cấu hình được phân tách bằng dấu chấm, ví dụ "SYSTEM_OPTIONS.NETWORK.MQTT_INFO"
        """
        try:
            value = self._config
            for key in path.split("."):
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def update_config(self, path: str, value: Any) -> bool:
        """
        Cập nhật mục cấu hình cụ thể
        path: Đường dẫn cấu hình được phân tách bằng dấu chấm, ví dụ "SYSTEM_OPTIONS.NETWORK.MQTT_INFO"
        """
        try:
            current = self._config
            *parts, last = path.split(".")
            for part in parts:
                current = current.setdefault(part, {})
            current[last] = value
            return self._save_config(self._config)
        except Exception as e:
            logger.error(f"Lỗi cập nhật cấu hình {path}: {e}")
            return False

    def reload_config(self) -> bool:
        """
        Tải lại tệp cấu hình.
        """
        try:
            self._config = self._load_config()
            logger.info("Tệp cấu hình đã được tải lại")
            return True
        except Exception as e:
            logger.error(f"Tải lại cấu hình thất bại: {e}")
            return False

    def generate_uuid(self) -> str:
        """
        Tạo UUID v4.
        """
        return str(uuid.uuid4())

    def initialize_client_id(self):
        """
        Đảm bảo tồn tại ID máy khách.
        """
        if not self.get_config("SYSTEM_OPTIONS.CLIENT_ID"):
            client_id = self.generate_uuid()
            success = self.update_config("SYSTEM_OPTIONS.CLIENT_ID", client_id)
            if success:
                logger.info(f"Đã tạo ID máy khách mới: {client_id}")
            else:
                logger.error("Lưu ID máy khách mới thất bại")

    def initialize_device_id_from_fingerprint(self, device_fingerprint):
        """
        Khởi tạo ID thiết bị từ dấu vân tay thiết bị.
        """
        if not self.get_config("SYSTEM_OPTIONS.DEVICE_ID"):
            try:
                # 从efuse.json获取MAC地址作为DEVICE_ID
                mac_address = device_fingerprint.get_mac_address_from_efuse()
                if mac_address:
                    success = self.update_config(
                        "SYSTEM_OPTIONS.DEVICE_ID", mac_address
                    )
                    if success:
                        logger.info(f"Nhận DEVICE_ID từ efuse.json: {mac_address}")
                    else:
                        logger.error("Lưu DEVICE_ID thất bại")
                else:
                    logger.error("Không thể nhận địa chỉ MAC từ efuse.json")
                    # 备用方案：从设备指纹直接获取
                    fingerprint = device_fingerprint.generate_fingerprint()
                    mac_from_fingerprint = fingerprint.get("mac_address")
                    if mac_from_fingerprint:
                        success = self.update_config(
                            "SYSTEM_OPTIONS.DEVICE_ID", mac_from_fingerprint
                        )
                        if success:
                            logger.info(
                                f"Sử dụng địa chỉ MAC trong dấu vân tay làm DEVICE_ID: "
                                f"{mac_from_fingerprint}"
                            )
                        else:
                            logger.error("Lưu DEVICE_ID dự phòng thất bại")
            except Exception as e:
                logger.error(f"Lỗi khi khởi tạo DEVICE_ID: {e}")

    @classmethod
    def get_instance(cls):
        """
        Lấy thể hiện trình quản lý cấu hình.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
