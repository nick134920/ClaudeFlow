import yaml
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config.yaml"


def load_config() -> dict:
    """加载 YAML 配置文件"""
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


_config = load_config()

# 全局配置
API_KEY: str = _config.get("api_key", "")
LOG_DIR: Path = BASE_DIR / _config.get("log_dir", "logs")
LOG_LEVEL: str = _config.get("log_level", "INFO")


def get_agent_config(agent_name: str) -> dict:
    """获取指定 agent 的配置"""
    return _config.get(agent_name, {})
