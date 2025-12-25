# Notion 写入迁移设计：MCP 到 SDK

## 概述

将项目中 DeepResearch 和 NewProjectAnalyse 两个 Agent 的 Notion 写入方式从 MCP 工具调用迁移到 notion-sdk-py 直接 SDK 调用，提高写入可靠性。

## 架构变更

### 迁移前

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Lead Agent     │────▶│ notion-writer    │────▶│ Notion MCP  │
│  (DeepResearch) │     │ SubAgent         │     │ Server      │
└─────────────────┘     └──────────────────┘     └─────────────┘
```

### 迁移后

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Lead Agent     │────▶│ 主程序解析 JSON  │────▶│ Notion SDK  │
│  输出结构化JSON │     │ 调用服务模块     │     │ (直接API)   │
└─────────────────┘     └──────────────────┘     └─────────────┘
```

### 关键变更

1. 移除 `notion-writer` SubAgent
2. 新增 `app/services/notion.py` 共享服务模块
3. 修改 Lead Agent prompt，输出结构化 JSON
4. 统一 DeepResearch 和 NewProjectAnalyse 的输出格式
5. 移除 Notion MCP 服务器配置

---

## Notion 服务模块设计

### 文件位置

`app/services/notion.py`

### 类设计

```python
class NotionService:
    """Notion API 封装服务"""

    def __init__(self, token: str):
        """初始化 Notion Client"""

    def create_page(
        self,
        parent_page_id: str,
        title: str,
        blocks: list[dict]
    ) -> str:
        """
        创建新页面并写入内容
        返回: 新页面 ID
        """

    def append_blocks(
        self,
        page_id: str,
        blocks: list[dict]
    ) -> None:
        """向现有页面追加块内容"""


class BlockBuilder:
    """块类型构建辅助类"""

    @staticmethod
    def paragraph(text: str) -> dict

    @staticmethod
    def heading(level: int, text: str) -> dict  # 1, 2, 3

    @staticmethod
    def bulleted_list(items: list[str]) -> list[dict]

    @staticmethod
    def numbered_list(items: list[str]) -> list[dict]

    @staticmethod
    def code(code: str, language: str = "plain text") -> dict

    @staticmethod
    def divider() -> dict

    @staticmethod
    def to_do(text: str, checked: bool = False) -> dict
```

### 错误处理

```python
class NotionWriteError(Exception):
    """Notion 写入失败异常"""

# 重试配置
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # 指数退避（秒）
```

---

## Agent 输出 Schema 设计

### 统一输出格式

两个 Agent 都输出相同结构的 JSON：

```json
{
    "title": "页面标题",
    "blocks": [
        {"type": "heading_1", "content": "一级标题"},
        {"type": "heading_2", "content": "二级标题"},
        {"type": "heading_3", "content": "三级标题"},
        {"type": "paragraph", "content": "段落文本内容"},
        {"type": "bulleted_list", "items": ["项目1", "项目2", "项目3"]},
        {"type": "numbered_list", "items": ["步骤1", "步骤2"]},
        {"type": "code", "content": "代码内容", "language": "python"},
        {"type": "divider"},
        {"type": "to_do", "content": "待办事项", "checked": false}
    ]
}
```

### Schema 解析流程

```python
def parse_agent_output(output: str) -> dict:
    """
    从 Agent 输出中提取 JSON
    处理可能的 markdown 代码块包裹
    """

def blocks_to_notion_format(blocks: list[dict]) -> list[dict]:
    """
    将简化 schema 转换为 Notion API 格式
    使用 BlockBuilder 构建各类型块
    """
```

---

## 配置变更

### config.yaml 新结构

```yaml
agents:
  deepresearch:
    model: sonnet
    max_turns: 50
    notion:
      token: "deepresearch-notion-token"
      parent_page_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

  newprojectanalyse:
    model: sonnet
    max_turns: 30
    notion:
      token: "newprojectanalyse-notion-token"
      parent_page_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

### 移除配置

从 `mcp_servers` 中移除 `notion` 配置块。

### 配置读取

```python
# app/config.py
def get_agent_notion_config(agent_name: str) -> dict:
    """
    获取指定 Agent 的 Notion 配置
    返回: {"token": "...", "parent_page_id": "..."}
    """
```

---

## 代码变更清单

### 新增文件

| 文件 | 说明 |
|------|------|
| `app/services/notion.py` | Notion 服务模块 |
| `app/services/__init__.py` | 服务模块初始化 |

### 修改文件

| 文件 | 变更内容 |
|------|----------|
| `app/agents/deepresearch/agent.py` | 移除 notion-writer SubAgent，新增 JSON 解析和 Notion 写入调用 |
| `app/agents/deepresearch/prompts/lead_agent.py` | 修改输出要求为结构化 JSON |
| `app/agents/newprojectanalyse/agent.py` | 移除 MCP 工具调用，新增 JSON 解析和 Notion 写入调用 |
| `app/config.py` | 新增 `get_agent_notion_config()` 方法 |
| `config.yaml.example` | 更新配置示例 |
| `requirements.txt` | 新增 `notion-client` 依赖 |

### 删除文件

| 文件 | 说明 |
|------|------|
| `app/agents/deepresearch/prompts/notion_writer.py` | 不再需要 SubAgent prompt |

### 删除代码

- `agent.py` 中 `notion-writer` SubAgent 定义
- `config.yaml.example` 中 `mcp_servers.notion` 配置块
