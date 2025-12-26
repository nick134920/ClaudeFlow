from app.config import get_agent_config, get_agent_notion_config

_config = get_agent_config("deepresearch")

# 基础配置
MODEL: str = _config.get("model", "claude-sonnet-4-20250514")
MAX_TURNS: int = _config.get("max_turns", 20)
# researcher subagent model: sonnet | haiku | opus
RESEARCHER_MODEL: str = _config.get("researcher_model", "haiku")

# Notion 配置
_notion_config = get_agent_notion_config("deepresearch")
NOTION_TOKEN: str = _notion_config.get("token", "")
NOTION_PARENT_PAGE_ID: str = _notion_config.get("parent_page_id", "")

# Tavily 配置
TAVILY_CONFIG: dict = _config.get("tavily", {})
SEARCH_DEPTH: str = TAVILY_CONFIG.get("search_depth", "advanced")
MAX_RESULTS: int = TAVILY_CONFIG.get("max_results", 10)
INCLUDE_IMAGES: bool = TAVILY_CONFIG.get("include_images", False)

# MCP 服务器配置（移除 notion）
MCP_SERVERS: dict = _config.get("mcp_servers", {})
