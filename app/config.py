import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 全局配置
API_KEY: str = os.getenv("API_KEY", "")
LOG_DIR: Path = BASE_DIR / os.getenv("LOG_DIR", "logs")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
