# NewProjectAnalyse 重构实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 NewProjectAnalyseAgent 拆分为 GitHub 和 Web 两个独立 handler，采用 SDK Subagent 机制实现协作。

**Architecture:** 入口 agent 负责预处理和分发，通过 AgentDefinition 定义 subagent，Prompt 层决定调用哪个 subagent，入口 agent 聚合结果后写入 Notion。

**Tech Stack:** Python, claude_agent_sdk (AgentDefinition), gitingest, Notion API

---

## Task 1: 创建 prompts 目录结构

**Files:**
- Create: `app/agents/newprojectanalyse/prompts/__init__.py`
- Create: `app/agents/newprojectanalyse/prompts/github.py`
- Create: `app/agents/newprojectanalyse/prompts/web.py`
- Create: `app/agents/newprojectanalyse/prompts/dispatcher.py`

**Step 1: 创建 prompts 目录和 __init__.py**

```bash
mkdir -p app/agents/newprojectanalyse/prompts
```

```python
# app/agents/newprojectanalyse/prompts/__init__.py
from app.agents.newprojectanalyse.prompts.dispatcher import get_dispatcher_prompt
from app.agents.newprojectanalyse.prompts.github import get_github_prompt
from app.agents.newprojectanalyse.prompts.web import get_web_prompt

__all__ = ["get_dispatcher_prompt", "get_github_prompt", "get_web_prompt"]
```

**Step 2: 创建 prompts/github.py**

从 agent.py 的 `get_prompt_for_github` 方法提取：

```python
# app/agents/newprojectanalyse/prompts/github.py
from datetime import datetime


def get_github_prompt(url: str, summary: str, content: str) -> str:
    """获取 GitHub 仓库分析的 Prompt"""
    current_date = datetime.now().strftime("%Y%m%d")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""
请分析以下 GitHub 仓库：{url}

## 仓库信息（由 gitingest 获取）

### 概要
{summary}

### 文件内容
{content}

## 任务

1. 从 URL 中提取 owner 和 repo，使用 GitHub API 获取项目统计信息：
   - 访问 https://api.github.com/repos/{{owner}}/{{repo}} 获取 star、fork 数量和最后更新时间
   - 访问 https://api.github.com/repos/{{owner}}/{{repo}}/commits?per_page=1 获取最后 commit 时间

2. 基于以上内容，生成项目总结

3. 识别项目名称，并生成一个简洁的中文标题（10字以内）

4. 将内容总结并输出为以下 JSON 格式（必须用 ```json 包裹）：

```json
{{
  "title": "项目名称-中文标题-{current_date}",
  "blocks": [
    {{"type": "bookmark", "url": "{url}"}},
    {{"type": "callout", "content": "⭐ Stars: 1234 | 🍴 Forks: 567 | 📅 最后提交: 2024-01-01", "emoji": "📊"}},
    {{"type": "divider"}},
    {{"type": "heading_1", "content": "项目概述"}},
    {{"type": "paragraph", "content": "项目简介..."}},
    {{"type": "heading_1", "content": "核心要点"}},
    {{"type": "bulleted_list", "items": ["要点1", "要点2", "要点3", "要点4", "要点5"]}},
    {{"type": "heading_1", "content": "详细总结"}},
    {{"type": "paragraph", "content": "200-300字的详细总结..."}},
    {{"type": "heading_1", "content": "核心逻辑思维导图"}},
    {{"type": "bulleted_list", "items": [
      {{"text": "主要模块1", "children": ["子模块1.1", "子模块1.2"]}},
      {{"text": "主要模块2", "children": ["子模块2.1", "子模块2.2"]}}
    ]}},
    {{"type": "heading_1", "content": "部署说明"}},
    {{"type": "bulleted_list", "items": ["环境要求: ...", "安装步骤: ...", "启动命令: ..."]}},
    {{"type": "divider"}},
    {{"type": "paragraph", "content": "任务时间: {current_time}"}}
  ]
}}
```

**支持的块类型:**
- heading_1, heading_2, heading_3: 标题（content 字段）
- paragraph: 段落（content 字段）
- bulleted_list: 无序列表，支持两种格式:
  - 简单列表: items 为字符串数组 ["item1", "item2"]
  - 嵌套列表: items 为对象数组 [{{"text": "父项", "children": ["子项1", "子项2"]}}]
- numbered_list: 有序列表（items 字段，字符串数组）
- code: 代码块（content 和 language 字段）
- divider: 分割线（无额外字段）
- bookmark: 书签链接（url 字段）
- callout: 标注块（content 和 emoji 字段）
- to_do: 待办事项（content 和 checked 字段）

**重要:**
- 使用 mcp__fetch__fetch 工具访问 GitHub API 获取统计信息
- title 格式必须为: "项目名称-中文标题-{current_date}"
- 必须获取并显示 star/fork/最后提交时间，使用 callout 块展示
- 部署说明从 README、Dockerfile、package.json 等文件中提取
- 任务时间必须放在内容最后
- 最终必须输出上述 JSON 格式
- JSON 必须用 ```json 代码块包裹
- 确保 JSON 格式正确，可以被解析
"""
```

**Step 3: 创建 prompts/web.py**

从 agent.py 的 `get_prompt_for_web` 方法提取：

```python
# app/agents/newprojectanalyse/prompts/web.py
from datetime import datetime


def get_web_prompt(url: str) -> str:
    """获取网页分析的 Prompt"""
    current_date = datetime.now().strftime("%Y%m%d")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""
请完成以下任务：

1. 使用 mcp__firecrawl__firecrawl_scrape 工具抓取这个 URL 的内容：{url}

2. 识别网站/文章的名称，并生成一个简洁的中文标题（10字以内）

3. 分析网页内容，提取核心信息并总结

4. 将内容总结并输出为以下 JSON 格式（必须用 ```json 包裹）：

```json
{{
  "title": "网站名称-中文标题-{current_date}",
  "blocks": [
    {{"type": "bookmark", "url": "{url}"}},
    {{"type": "divider"}},
    {{"type": "heading_1", "content": "内容概述"}},
    {{"type": "paragraph", "content": "网页内容的简要概述..."}},
    {{"type": "heading_1", "content": "核心要点"}},
    {{"type": "bulleted_list", "items": ["要点1", "要点2", "要点3", "要点4", "要点5"]}},
    {{"type": "heading_1", "content": "详细总结"}},
    {{"type": "paragraph", "content": "200-300字的详细总结，包含主要观点、关键信息等..."}},
    {{"type": "heading_1", "content": "内容结构"}},
    {{"type": "bulleted_list", "items": [
      {{"text": "主要章节1", "children": ["子内容1.1", "子内容1.2"]}},
      {{"text": "主要章节2", "children": ["子内容2.1", "子内容2.2"]}}
    ]}},
    {{"type": "divider"}},
    {{"type": "paragraph", "content": "任务时间: {current_time}"}}
  ]
}}
```

**支持的块类型:**
- heading_1, heading_2, heading_3: 标题（content 字段）
- paragraph: 段落（content 字段）
- bulleted_list: 无序列表，支持两种格式:
  - 简单列表: items 为字符串数组 ["item1", "item2"]
  - 嵌套列表: items 为对象数组 [{{"text": "父项", "children": ["子项1", "子项2"]}}]
- numbered_list: 有序列表（items 字段，字符串数组）
- code: 代码块（content 和 language 字段）
- divider: 分割线（无额外字段）
- bookmark: 书签链接（url 字段）
- callout: 标注块（content 和 emoji 字段）
- to_do: 待办事项（content 和 checked 字段）

**重要:**
- title 格式必须为: "网站名称-中文标题-{current_date}"
- 任务时间必须放在内容最后
- 最终必须输出上述 JSON 格式
- JSON 必须用 ```json 代码块包裹
- 确保 JSON 格式正确，可以被解析
"""
```

**Step 4: 创建 prompts/dispatcher.py**

```python
# app/agents/newprojectanalyse/prompts/dispatcher.py

def get_dispatcher_prompt(url: str, github_content: tuple[str, str, str] | None) -> str:
    """
    入口 agent 的分发 prompt

    Args:
        url: 目标 URL
        github_content: GitHub 仓库内容 (summary, tree, content)，如果是 GitHub URL 且预获取成功
    """
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

**Step 5: Commit**

```bash
git add app/agents/newprojectanalyse/prompts/
git commit -m "feat(newprojectanalyse): 添加 prompts 模块"
```

---

## Task 2: 创建 handlers 目录结构

**Files:**
- Create: `app/agents/newprojectanalyse/handlers/__init__.py`
- Create: `app/agents/newprojectanalyse/handlers/github.py`
- Create: `app/agents/newprojectanalyse/handlers/web.py`

**Step 1: 创建 handlers 目录和 __init__.py**

```bash
mkdir -p app/agents/newprojectanalyse/handlers
```

```python
# app/agents/newprojectanalyse/handlers/__init__.py
from app.agents.newprojectanalyse.handlers.github import get_github_agent_definition
from app.agents.newprojectanalyse.handlers.web import get_web_agent_definition

__all__ = ["get_github_agent_definition", "get_web_agent_definition"]
```

**Step 2: 创建 handlers/github.py**

```python
# app/agents/newprojectanalyse/handlers/github.py
from claude_agent_sdk import AgentDefinition

from app.agents.newprojectanalyse.prompts.github import get_github_prompt


def get_github_agent_definition(url: str, summary: str, content: str) -> AgentDefinition:
    """
    返回 GitHub 分析 subagent 的定义

    Args:
        url: GitHub 仓库 URL
        summary: gitingest 获取的仓库概要
        content: gitingest 获取的文件内容
    """
    return AgentDefinition(
        description="分析 GitHub 仓库，提取项目信息、技术栈、部署说明等",
        prompt=get_github_prompt(url, summary, content),
        tools=["mcp__fetch__fetch"],
        model="sonnet",
    )
```

**Step 3: 创建 handlers/web.py**

```python
# app/agents/newprojectanalyse/handlers/web.py
from claude_agent_sdk import AgentDefinition

from app.agents.newprojectanalyse.prompts.web import get_web_prompt


def get_web_agent_definition(url: str) -> AgentDefinition:
    """
    返回 Web 分析 subagent 的定义

    Args:
        url: 网页 URL
    """
    return AgentDefinition(
        description="分析网页内容，提取核心信息并总结",
        prompt=get_web_prompt(url),
        tools=["mcp__firecrawl__firecrawl_scrape"],
        model="sonnet",
    )
```

**Step 4: Commit**

```bash
git add app/agents/newprojectanalyse/handlers/
git commit -m "feat(newprojectanalyse): 添加 handlers 模块"
```

---

## Task 3: 更新 config.py

**Files:**
- Modify: `app/agents/newprojectanalyse/config.py`

**Step 1: 将 GitHub patterns 从 agent.py 移到 config.py**

```python
# app/agents/newprojectanalyse/config.py
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

**Step 2: Commit**

```bash
git add app/agents/newprojectanalyse/config.py
git commit -m "feat(newprojectanalyse): 将 GitHub patterns 移至 config"
```

---

## Task 4: 重构 agent.py

**Files:**
- Modify: `app/agents/newprojectanalyse/agent.py`

**Step 1: 重写 agent.py 为入口分发器**

```python
# app/agents/newprojectanalyse/agent.py
import re

from claude_agent_sdk import ClaudeAgentOptions

from app.agents.base import BaseAgent
from app.agents.newprojectanalyse.config import (
    MODEL,
    NOTION_TOKEN,
    NOTION_PARENT_PAGE_ID,
    MAX_TURNS,
    MCP_SERVERS,
    GITHUB_EXCLUDE_PATTERNS,
    GITHUB_INCLUDE_PATTERNS,
)
from app.agents.newprojectanalyse.handlers import (
    get_github_agent_definition,
    get_web_agent_definition,
)
from app.agents.newprojectanalyse.prompts import get_dispatcher_prompt
from app.services.notion import (
    NotionService,
    parse_agent_output,
    blocks_to_notion_format,
)


def is_github_repo_url(url: str) -> bool:
    """判断是否为 GitHub 仓库 URL"""
    pattern = r'^https?://github\.com/[\w.-]+/[\w.-]+/?'
    return bool(re.match(pattern, url))


async def fetch_github_repo_content(url: str) -> tuple[str, str, str]:
    """
    获取 GitHub 仓库内容

    Args:
        url: GitHub 仓库 URL

    Returns:
        tuple: (summary, tree, content)
    """
    from gitingest import ingest_async

    summary, tree, content = await ingest_async(
        url,
        include_patterns=GITHUB_INCLUDE_PATTERNS,
        exclude_patterns=GITHUB_EXCLUDE_PATTERNS,
    )
    return summary, tree, content


class NewProjectAnalyseAgent(BaseAgent):
    """新项目分析 Agent - 入口分发器"""

    MODULE_NAME = "newprojectanalyse"

    def __init__(self):
        super().__init__()
        self._url: str = ""
        self._github_content: tuple[str, str, str] | None = None

    async def pre_run(self, logger, **kwargs) -> dict:
        """
        运行前预处理：判断是否为 GitHub 仓库并获取内容

        Args:
            logger: TaskLogger 实例
            **kwargs: 包含 url 参数

        Returns:
            dict: 包含 github_content 的额外参数
        """
        url = kwargs.get("url")
        if not url:
            raise ValueError("url 参数是必需的")

        self._url = url
        self._github_content = None

        if is_github_repo_url(url):
            logger.info("检测到 GitHub 仓库 URL，使用 gitingest 获取内容...")
            try:
                self._github_content = await fetch_github_repo_content(url)
                logger.info("gitingest 获取成功")
            except Exception as e:
                logger.warning(f"gitingest 获取失败，回退到 web 分析: {e}")
                self._github_content = None

        return {"github_content": self._github_content}

    def get_prompt(self, url: str, github_content: tuple[str, str, str] | None = None, **kwargs) -> str:
        """生成入口 agent 的分发 prompt"""
        return get_dispatcher_prompt(url, github_content)

    def get_options(self) -> ClaudeAgentOptions:
        """注册所有 subagent"""
        agents = {}

        if self._github_content:
            summary, _tree, content = self._github_content
            agents["github_analyser"] = get_github_agent_definition(
                self._url, summary, content
            )
        else:
            agents["web_analyser"] = get_web_agent_definition(self._url)

        return ClaudeAgentOptions(
            model=MODEL,
            max_turns=MAX_TURNS,
            permission_mode="bypassPermissions",
            mcp_servers=MCP_SERVERS,
            agents=agents,
            allowed_tools=["Task"],
        )

    def get_input_data(self, url: str) -> dict:
        return {"url": url}

    async def process_final_output(self, final_text: str, **kwargs) -> None:
        """聚合 subagent 结果，写入 Notion"""
        if not final_text:
            return

        parsed = parse_agent_output(final_text)
        notion_blocks = blocks_to_notion_format(parsed["blocks"])

        notion_service = NotionService(NOTION_TOKEN)
        notion_service.create_page(
            parent_page_id=NOTION_PARENT_PAGE_ID,
            title=parsed["title"],
            blocks=notion_blocks,
        )


async def run_newprojectanalyse_agent(url: str) -> None:
    """执行 newprojectanalyse Agent"""
    agent = NewProjectAnalyseAgent()
    await agent.run(url=url)
```

**Step 2: Commit**

```bash
git add app/agents/newprojectanalyse/agent.py
git commit -m "refactor(newprojectanalyse): 重构为入口分发器模式"
```

---

## Task 5: 更新 __init__.py 导出

**Files:**
- Modify: `app/agents/newprojectanalyse/__init__.py`

**Step 1: 更新模块导出**

```python
# app/agents/newprojectanalyse/__init__.py
from app.agents.newprojectanalyse.agent import (
    NewProjectAnalyseAgent,
    run_newprojectanalyse_agent,
)

__all__ = ["NewProjectAnalyseAgent", "run_newprojectanalyse_agent"]
```

**Step 2: Commit**

```bash
git add app/agents/newprojectanalyse/__init__.py
git commit -m "refactor(newprojectanalyse): 更新模块导出"
```

---

## Task 6: 验证重构

**Step 1: 检查 Python 语法**

```bash
cd /Users/nick/Syncthing/Develop/AI/ClaudeFlow
python -m py_compile app/agents/newprojectanalyse/agent.py
python -m py_compile app/agents/newprojectanalyse/config.py
python -m py_compile app/agents/newprojectanalyse/prompts/__init__.py
python -m py_compile app/agents/newprojectanalyse/prompts/dispatcher.py
python -m py_compile app/agents/newprojectanalyse/prompts/github.py
python -m py_compile app/agents/newprojectanalyse/prompts/web.py
python -m py_compile app/agents/newprojectanalyse/handlers/__init__.py
python -m py_compile app/agents/newprojectanalyse/handlers/github.py
python -m py_compile app/agents/newprojectanalyse/handlers/web.py
```

Expected: 无输出表示语法正确

**Step 2: 检查导入**

```bash
cd /Users/nick/Syncthing/Develop/AI/ClaudeFlow
python -c "from app.agents.newprojectanalyse import NewProjectAnalyseAgent, run_newprojectanalyse_agent; print('Import OK')"
```

Expected: `Import OK`

**Step 3: 最终 Commit**

```bash
git add -A
git commit -m "feat(newprojectanalyse): 完成 GitHub/Web handler 拆分重构"
```

---

## 文件清单

| 操作 | 文件路径 |
|------|----------|
| Create | `app/agents/newprojectanalyse/prompts/__init__.py` |
| Create | `app/agents/newprojectanalyse/prompts/dispatcher.py` |
| Create | `app/agents/newprojectanalyse/prompts/github.py` |
| Create | `app/agents/newprojectanalyse/prompts/web.py` |
| Create | `app/agents/newprojectanalyse/handlers/__init__.py` |
| Create | `app/agents/newprojectanalyse/handlers/github.py` |
| Create | `app/agents/newprojectanalyse/handlers/web.py` |
| Modify | `app/agents/newprojectanalyse/config.py` |
| Modify | `app/agents/newprojectanalyse/agent.py` |
| Modify | `app/agents/newprojectanalyse/__init__.py` |
