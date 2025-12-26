from app.config import get_agent_config, get_agent_notion_config

_agent_config = get_agent_config("newprojectanalyse")

# 通用配置
MODEL: str = _agent_config.get("model", "claude-sonnet-4-20250514")
MAX_TURNS: int = _agent_config.get("max_turns", 15)
# subagent model: sonnet | haiku | opus
SUBAGENT_MODEL: str = _agent_config.get("subagent_model", "sonnet")

# Notion 配置
_notion_config = get_agent_notion_config("newprojectanalyse")
NOTION_TOKEN: str = _notion_config.get("token", "")
NOTION_PARENT_PAGE_ID: str = _notion_config.get("parent_page_id", "")

# MCP 服务器配置
MCP_SERVERS: dict = _agent_config.get("mcp_servers", {})

# GitHub 预处理配置
GITHUB_EXCLUDE_PATTERNS: list = _agent_config.get("github_exclude_patterns", [
    "node_modules/*", "vendor/*", ".venv/*", "venv/*",
    "dist/*", "build/*", ".git/*",
    "*.lock", "*.min.js", "*.min.css",
    "*.log", "*.pyc", "__pycache__/*",
    "pnpm-lock.yaml", "package-lock.json", "bun.lockb",
])

GITHUB_INCLUDE_PATTERNS: list = _agent_config.get("github_include_patterns", [
    "README*", "readme*", "CHANGELOG*", "LICENSE*", "CONTRIBUTING*",
    "*.md", "docs/*.md", "docs/**/*.md",
    "package.json", "pyproject.toml", "setup.py", "setup.cfg",
    "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
    "Makefile", "Dockerfile", "docker-compose*.yml",
    "*.toml", "*.yaml", "*.yml", "*.json",
])
