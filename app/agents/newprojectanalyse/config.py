from app.config import get_agent_config

_agent_config = get_agent_config("newprojectanalyse")

# newprojectanalyse 模块配置
NOTION_PARENT_PAGE_ID: str = _agent_config.get("notion_parent_page_id", "")
MAX_TURNS: int = _agent_config.get("max_turns", 15)
MCP_SERVERS: dict = _agent_config.get("mcp_servers", {})
