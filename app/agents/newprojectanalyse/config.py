from app.config import get_agent_config, get_agent_notion_config

_agent_config = get_agent_config("newprojectanalyse")

# newprojectanalyse 模块配置
MODEL: str = _agent_config.get("model", "claude-sonnet-4-20250514")
MAX_TURNS: int = _agent_config.get("max_turns", 15)

# Notion 配置
_notion_config = get_agent_notion_config("newprojectanalyse")
NOTION_TOKEN: str = _notion_config.get("token", "")
NOTION_PARENT_PAGE_ID: str = _notion_config.get("parent_page_id", "")

# MCP 服务器配置（移除 notion）
MCP_SERVERS: dict = _agent_config.get("mcp_servers", {})
