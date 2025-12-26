# NewProjectAnalyse 重构设计

## 概述

将 `NewProjectAnalyseAgent` 拆分为 GitHub 和 Web 两个独立 handler，采用 SDK Subagent 机制实现协作，保持工程化结构便于后续扩展。

## 设计决策

| 决策点 | 选择 |
|--------|------|
| 架构模式 | 入口 agent 分发给 subagent |
| 目录结构 | handlers + prompts 分离 |
| Subagent 实现 | SDK AgentDefinition（不独立运行） |
| 路由方式 | Prompt 层判断 |
| GitHub 预处理 | 保留 gitingest 预获取 |
| 输出处理 | 入口 agent 聚合后写入 Notion |
| 配置管理 | 统一 config.py |

## 目录结构

```
app/agents/newprojectanalyse/
├── __init__.py
├── agent.py           # 入口 agent (NewProjectAnalyseAgent)
├── config.py          # 统一配置
├── handlers/
│   ├── __init__.py
│   ├── github.py      # GitHub handler: AgentDefinition
│   └── web.py         # Web handler: AgentDefinition
└── prompts/
    ├── __init__.py
    ├── dispatcher.py  # 入口 agent 的分发 prompt
    ├── github.py      # GitHub 分析 prompt 模板
    └── web.py         # Web 分析 prompt 模板
```

## 入口 Agent 架构

```python
# agent.py
class NewProjectAnalyseAgent(BaseAgent):
    MODULE_NAME = "newprojectanalyse"

    async def pre_run(self, logger, url: str, **kwargs) -> dict:
        """预处理：如果是 GitHub URL，预获取内容"""
        github_content = None
        if is_github_repo_url(url):
            logger.info("检测到 GitHub 仓库，预获取内容...")
            github_content = await fetch_github_repo_content(url)
        return {"github_content": github_content}

    def get_prompt(self, url: str, github_content=None, **kwargs) -> str:
        """生成入口 agent 的 prompt"""
        return get_dispatcher_prompt(url, github_content)

    def get_options(self) -> ClaudeAgentOptions:
        """注册所有 subagent"""
        agents = {
            "github_analyser": get_github_agent_definition(),
            "web_analyser": get_web_agent_definition(),
        }
        return ClaudeAgentOptions(
            model=MODEL,
            max_turns=MAX_TURNS,
            agents=agents,
            allowed_tools=["Task"],
            permission_mode="bypassPermissions",
            mcp_servers=MCP_SERVERS,
        )

    async def process_final_output(self, final_text: str, **kwargs):
        """聚合 subagent 结果，写入 Notion"""
        parsed = parse_agent_output(final_text)
        notion_blocks = blocks_to_notion_format(parsed["blocks"])
        notion_service = NotionService(NOTION_TOKEN)
        notion_service.create_page(
            parent_page_id=NOTION_PARENT_PAGE_ID,
            title=parsed["title"],
            blocks=notion_blocks,
        )
```

## Handlers 实现

```python
# handlers/github.py
from claude_agent_sdk import AgentDefinition
from app.agents.newprojectanalyse.prompts.github import get_github_prompt

def get_github_agent_definition() -> AgentDefinition:
    """返回 GitHub 分析 subagent 的定义"""
    return AgentDefinition(
        description="分析 GitHub 仓库，提取项目信息、技术栈、部署说明等",
        prompt=get_github_prompt(),
        tools=["mcp__fetch__fetch"],
        model="sonnet",
    )
```

```python
# handlers/web.py
from claude_agent_sdk import AgentDefinition
from app.agents.newprojectanalyse.prompts.web import get_web_prompt

def get_web_agent_definition() -> AgentDefinition:
    """返回 Web 分析 subagent 的定义"""
    return AgentDefinition(
        description="分析网页内容，提取核心信息并总结",
        prompt=get_web_prompt(),
        tools=["mcp__firecrawl__firecrawl_scrape"],
        model="sonnet",
    )
```

## Prompts 实现

### dispatcher.py

```python
def get_dispatcher_prompt(url: str, github_content: tuple | None) -> str:
    """入口 agent 的分发 prompt"""
    context = ""
    if github_content:
        summary, _tree, content = github_content
        context = f"""
## 预获取的 GitHub 仓库内容
### 概要
{summary}
### 文件内容
{content}
"""

    return f"""
请分析以下 URL：{url}

{context}

## 任务
根据 URL 类型选择合适的分析方式：

1. 如果是 GitHub 仓库（已提供预获取内容），调用 github_analyser
2. 如果是普通网页，调用 web_analyser

调用对应的 subagent 完成分析，将其返回的结果直接作为最终输出。

## 输出格式
将 subagent 返回的 JSON 结果原样输出，格式：
```json
{{"title": "...", "blocks": [...]}}
```
"""
```

### github.py / web.py

沿用现有的 `get_prompt_for_github` / `get_prompt_for_web` 逻辑，移动到独立文件。

## 配置组织

```python
# config.py
from app.config import get_agent_config, get_agent_notion_config

_agent_config = get_agent_config("newprojectanalyse")

# 通用配置
MODEL: str = _agent_config.get("model", "claude-sonnet-4-20250514")
MAX_TURNS: int = _agent_config.get("max_turns", 15)

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
```

## 数据流

```
用户调用 run(url="https://...")
        ↓
    pre_run()
    ├─ 检测 URL 类型
    └─ GitHub? → gitingest 预获取内容
        ↓
    get_prompt()
    └─ 生成 dispatcher prompt（含预获取内容）
        ↓
    SDK 执行入口 agent
    └─ AI 判断 URL 类型 → 调用对应 subagent
        ↓
    subagent 执行分析
    └─ 返回 JSON 结果给入口 agent
        ↓
    入口 agent 输出最终 JSON
        ↓
    process_final_output()
    └─ 解析 JSON → 写入 Notion
```

## 扩展指南

新增 handler 步骤：

1. 创建 `prompts/new_type.py` - 定义分析 prompt
2. 创建 `handlers/new_type.py` - 定义 AgentDefinition
3. 在 `agent.py` 的 `get_options()` 中注册新 subagent
4. 更新 dispatcher prompt 添加新的路由条件
