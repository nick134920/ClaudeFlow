from app.config import get_agent_config

_config = get_agent_config("deepresearch")

# 基础配置
MODEL: str = _config.get("model", "claude-sonnet-4-20250514")
NOTION_PARENT_PAGE_ID: str = _config.get("notion_parent_page_id", "")
MAX_TURNS: int = _config.get("max_turns", 20)

# Tavily 配置
TAVILY_CONFIG: dict = _config.get("tavily", {})
SEARCH_DEPTH: str = TAVILY_CONFIG.get("search_depth", "advanced")
MAX_RESULTS: int = TAVILY_CONFIG.get("max_results", 10)
INCLUDE_IMAGES: bool = TAVILY_CONFIG.get("include_images", False)

# MCP 服务器配置
MCP_SERVERS: dict = _config.get("mcp_servers", {})
