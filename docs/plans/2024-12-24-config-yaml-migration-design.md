# 配置迁移设计：从 .env 到 config.yaml

## 概述

将项目配置方式从 `.env` 环境变量迁移到 `config.yaml`，包括 MCP 服务器配置。

## 配置文件结构

```yaml
# 全局配置
api_key: your-secret-key
log_dir: logs
log_level: INFO

# newprojectanalyse agent 配置
newprojectanalyse:
  notion_parent_page_id: REDACTED_NOTION_PAGE_ID
  max_turns: 15
  mcp_servers:
    firecrawl:
      type: stdio
      command: npx
      args: ["-y", "firecrawl-mcp"]
      env:
        FIRECRAWL_API_KEY: fc-xxx
    notion:
      type: stdio
      command: npx
      args: ["-y", "@notionhq/notion-mcp-server"]
      env:
        NOTION_TOKEN: ntn_xxx
```

## 代码变更

### app/config.py

```python
import yaml
from pathlib import Path

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
```

### app/agents/newprojectanalyse/config.py

```python
from app.config import get_agent_config

_agent_config = get_agent_config("newprojectanalyse")

NOTION_PARENT_PAGE_ID: str = _agent_config.get("notion_parent_page_id", "")
MAX_TURNS: int = _agent_config.get("max_turns", 15)
MCP_SERVERS: dict = _agent_config.get("mcp_servers", {})
```

### app/agents/newprojectanalyse/agent.py

- 删除硬编码的 `MCP_SERVERS` 字典
- 从 `config.py` 导入 `MCP_SERVERS`

## 文件变更清单

| 操作 | 文件 |
|------|------|
| 新增 | `config.yaml` |
| 新增 | `config.yaml.example` |
| 修改 | `app/config.py` |
| 修改 | `app/agents/newprojectanalyse/config.py` |
| 修改 | `app/agents/newprojectanalyse/agent.py` |
| 修改 | `requirements.txt` |
| 修改 | `.gitignore` |
| 删除 | `.env` |
| 删除 | `.env.example` |

## 依赖变更

- 移除：`python-dotenv`
- 新增：`pyyaml`
