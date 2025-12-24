import os
from dotenv import load_dotenv

load_dotenv()

# newprojectanalyse 模块配置（使用 NEWPROJECTANALYSE_ 前缀）
NOTION_PARENT_PAGE_ID: str = os.getenv("NEWPROJECTANALYSE_NOTION_PARENT_PAGE_ID", "")
MAX_TURNS: int = int(os.getenv("NEWPROJECTANALYSE_MAX_TURNS", "15"))
