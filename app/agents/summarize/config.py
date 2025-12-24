import os
from dotenv import load_dotenv

load_dotenv()

# summarize 模块配置（使用 SUMMARIZE_ 前缀）
NOTION_PARENT_PAGE_ID: str = os.getenv("SUMMARIZE_NOTION_PARENT_PAGE_ID", "")
MAX_TURNS: int = int(os.getenv("SUMMARIZE_MAX_TURNS", "15"))
