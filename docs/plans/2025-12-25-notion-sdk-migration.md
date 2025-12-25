# Notion SDK 迁移实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 DeepResearch 和 NewProjectAnalyse 两个 Agent 的 Notion 写入从 MCP 工具迁移到 notion-sdk-py 直接 SDK 调用

**Architecture:** 创建共享的 Notion 服务模块，Agent 输出结构化 JSON，主程序解析后调用 SDK 写入。移除 notion-writer SubAgent。

**Tech Stack:** notion-client (notion-sdk-py), Python 3.x

---

## Task 1: 添加 notion-client 依赖

**Files:**
- Modify: `requirements.txt`

**Step 1: 添加依赖**

在 `requirements.txt` 末尾添加：

```
notion-client
```

**Step 2: 安装依赖**

Run: `cd /Users/nick/Syncthing/Develop/AI/claude-code-agent-sdk/.worktrees/notion-sdk-migration && source .venv/bin/activate && pip install notion-client -q`

Expected: 安装成功，无错误

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: 添加 notion-client 依赖"
```

---

## Task 2: 创建 Notion 服务模块

**Files:**
- Create: `app/services/__init__.py`
- Create: `app/services/notion.py`

**Step 1: 创建 services 包初始化文件**

创建 `app/services/__init__.py`：

```python
"""服务模块"""
```

**Step 2: 创建 Notion 服务模块**

创建 `app/services/notion.py`：

```python
"""Notion API 服务封装"""
import time
import logging
from typing import Optional

from notion_client import Client
from notion_client.errors import APIResponseError

logger = logging.getLogger(__name__)


class NotionWriteError(Exception):
    """Notion 写入失败异常"""
    pass


class BlockBuilder:
    """Notion 块类型构建辅助类"""

    @staticmethod
    def _rich_text(content: str) -> list:
        """构建 rich_text 数组"""
        return [{"type": "text", "text": {"content": content}}]

    @staticmethod
    def paragraph(text: str) -> dict:
        """构建段落块"""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": BlockBuilder._rich_text(text)}
        }

    @staticmethod
    def heading(level: int, text: str) -> dict:
        """构建标题块 (level: 1, 2, 3)"""
        if level not in (1, 2, 3):
            raise ValueError(f"标题级别必须是 1, 2, 3，收到: {level}")
        heading_type = f"heading_{level}"
        return {
            "object": "block",
            "type": heading_type,
            heading_type: {"rich_text": BlockBuilder._rich_text(text)}
        }

    @staticmethod
    def bulleted_list(items: list[str]) -> list[dict]:
        """构建无序列表块列表"""
        return [
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": BlockBuilder._rich_text(item)}
            }
            for item in items
        ]

    @staticmethod
    def numbered_list(items: list[str]) -> list[dict]:
        """构建有序列表块列表"""
        return [
            {
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": BlockBuilder._rich_text(item)}
            }
            for item in items
        ]

    @staticmethod
    def code(content: str, language: str = "plain text") -> dict:
        """构建代码块"""
        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": BlockBuilder._rich_text(content),
                "language": language
            }
        }

    @staticmethod
    def divider() -> dict:
        """构建分割线块"""
        return {
            "object": "block",
            "type": "divider",
            "divider": {}
        }

    @staticmethod
    def to_do(text: str, checked: bool = False) -> dict:
        """构建待办事项块"""
        return {
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": BlockBuilder._rich_text(text),
                "checked": checked
            }
        }


class NotionService:
    """Notion API 封装服务"""

    MAX_RETRIES = 3
    RETRY_DELAYS = [1, 2, 4]  # 指数退避（秒）

    def __init__(self, token: str):
        """初始化 Notion Client"""
        self.client = Client(auth=token)

    def _retry_operation(self, operation, *args, **kwargs):
        """带重试的操作执行"""
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                return operation(*args, **kwargs)
            except APIResponseError as e:
                last_error = e
                logger.warning(
                    f"Notion API 错误 (尝试 {attempt + 1}/{self.MAX_RETRIES}): {e}"
                )
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAYS[attempt]
                    logger.info(f"等待 {delay} 秒后重试...")
                    time.sleep(delay)
            except Exception as e:
                last_error = e
                logger.error(f"意外错误: {e}")
                raise NotionWriteError(f"Notion 操作失败: {e}") from e

        raise NotionWriteError(
            f"Notion 操作在 {self.MAX_RETRIES} 次重试后失败: {last_error}"
        ) from last_error

    def create_page(
        self,
        parent_page_id: str,
        title: str,
        blocks: list[dict]
    ) -> str:
        """
        创建新页面并写入内容

        Args:
            parent_page_id: 父页面 ID
            title: 页面标题
            blocks: Notion 块列表（已转换为 Notion API 格式）

        Returns:
            新页面 ID
        """
        logger.info(f"创建 Notion 页面: {title}")

        def _create():
            return self.client.pages.create(
                parent={"page_id": parent_page_id},
                properties={
                    "title": [{"text": {"content": title}}]
                },
                children=blocks
            )

        result = self._retry_operation(_create)
        page_id = result["id"]
        page_url = result.get("url", "")
        logger.info(f"页面创建成功: {page_id}, URL: {page_url}")
        return page_id

    def append_blocks(
        self,
        page_id: str,
        blocks: list[dict]
    ) -> None:
        """
        向现有页面追加块内容

        Args:
            page_id: 页面 ID
            blocks: Notion 块列表
        """
        logger.info(f"向页面 {page_id} 追加 {len(blocks)} 个块")

        def _append():
            return self.client.blocks.children.append(
                block_id=page_id,
                children=blocks
            )

        self._retry_operation(_append)
        logger.info("块追加成功")


def parse_agent_output(output: str) -> dict:
    """
    从 Agent 输出中提取 JSON

    Args:
        output: Agent 的文本输出

    Returns:
        解析后的字典 {"title": str, "blocks": list}
    """
    import json
    import re

    # 尝试提取 markdown 代码块中的 JSON
    code_block_pattern = r"```(?:json)?\s*\n?([\s\S]*?)\n?```"
    matches = re.findall(code_block_pattern, output)

    for match in matches:
        try:
            data = json.loads(match.strip())
            if "title" in data and "blocks" in data:
                return data
        except json.JSONDecodeError:
            continue

    # 尝试直接解析整个输出
    try:
        data = json.loads(output.strip())
        if "title" in data and "blocks" in data:
            return data
    except json.JSONDecodeError:
        pass

    raise ValueError("无法从 Agent 输出中解析有效的 JSON 结构")


def blocks_to_notion_format(blocks: list[dict]) -> list[dict]:
    """
    将简化 schema 转换为 Notion API 格式

    Args:
        blocks: 简化格式的块列表

    Returns:
        Notion API 格式的块列表
    """
    result = []
    for block in blocks:
        block_type = block.get("type")

        if block_type == "paragraph":
            result.append(BlockBuilder.paragraph(block.get("content", "")))

        elif block_type in ("heading_1", "heading_2", "heading_3"):
            level = int(block_type[-1])
            result.append(BlockBuilder.heading(level, block.get("content", "")))

        elif block_type == "bulleted_list":
            result.extend(BlockBuilder.bulleted_list(block.get("items", [])))

        elif block_type == "numbered_list":
            result.extend(BlockBuilder.numbered_list(block.get("items", [])))

        elif block_type == "code":
            result.append(BlockBuilder.code(
                block.get("content", ""),
                block.get("language", "plain text")
            ))

        elif block_type == "divider":
            result.append(BlockBuilder.divider())

        elif block_type == "to_do":
            result.append(BlockBuilder.to_do(
                block.get("content", ""),
                block.get("checked", False)
            ))

        else:
            logger.warning(f"未知的块类型: {block_type}，跳过")

    return result
```

**Step 3: Commit**

```bash
git add app/services/__init__.py app/services/notion.py
git commit -m "feat: 添加 Notion 服务模块"
```

---

## Task 3: 更新配置系统

**Files:**
- Modify: `app/config.py`
- Modify: `config.yaml.example`
- Modify: `app/agents/deepresearch/config.py`
- Modify: `app/agents/newprojectanalyse/config.py`

**Step 1: 更新 app/config.py**

在 `app/config.py` 末尾添加：

```python
def get_agent_notion_config(agent_name: str) -> dict:
    """
    获取指定 Agent 的 Notion 配置

    Args:
        agent_name: Agent 名称

    Returns:
        {"token": str, "parent_page_id": str}
    """
    agent_config = get_agent_config(agent_name)
    notion_config = agent_config.get("notion", {})
    return {
        "token": notion_config.get("token", ""),
        "parent_page_id": notion_config.get("parent_page_id", ""),
    }
```

**Step 2: 更新 config.yaml.example**

将文件内容替换为：

```yaml
# 全局配置
api_key: your-secret-key
log_dir: logs
log_level: INFO

# newprojectanalyse agent 配置
newprojectanalyse:
  model: claude-sonnet-4-20250514
  max_turns: 15
  notion:
    token: your-notion-token
    parent_page_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  mcp_servers:
    firecrawl:
      type: stdio
      command: npx
      args: ["-y", "firecrawl-mcp"]
      env:
        FIRECRAWL_API_KEY: your-firecrawl-api-key

# deepresearch agent 配置
deepresearch:
  model: claude-sonnet-4-20250514
  max_turns: 20
  notion:
    token: your-notion-token
    parent_page_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  tavily:
    search_depth: advanced
    max_results: 10
    include_images: false
  mcp_servers:
    tavily:
      type: stdio
      command: npx
      args: ["-y", "tavily-mcp@latest"]
      env:
        TAVILY_API_KEY: your-tavily-api-key
```

**Step 3: 更新 deepresearch/config.py**

将文件内容替换为：

```python
from app.config import get_agent_config, get_agent_notion_config

_config = get_agent_config("deepresearch")

# 基础配置
MODEL: str = _config.get("model", "claude-sonnet-4-20250514")
MAX_TURNS: int = _config.get("max_turns", 20)

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
```

**Step 4: 更新 newprojectanalyse/config.py**

将文件内容替换为：

```python
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
```

**Step 5: Commit**

```bash
git add app/config.py config.yaml.example app/agents/deepresearch/config.py app/agents/newprojectanalyse/config.py
git commit -m "refactor: 更新配置系统，添加独立 Notion 配置"
```

---

## Task 4: 更新 DeepResearch Lead Agent Prompt

**Files:**
- Modify: `app/agents/deepresearch/prompts/lead_agent.py`

**Step 1: 更新 prompt**

将文件内容替换为：

```python
LEAD_AGENT_PROMPT = """你是一个研究协调者，负责协调多 Agent 研究任务。

**研究主题:** {topic}

**关键规则:**
1. 你只能使用 Task 工具派发 researcher subagent，不能自己研究
2. 保持简洁，最多 2-3 句话
3. 立即开始工作，不要寒暄

**工作流程:**

**第一步：分解主题**
将研究主题分解为 2-4 个独立的子课题，每个子课题应该是主题的不同角度或方面。

**第二步：并行派发 Researcher**
使用 Task 工具并行派发多个 researcher subagent，每个负责一个子课题。

派发时使用:
- subagent_type: "researcher"
- description: 简短描述子课题（3-5 个词）
- prompt: 详细说明要研究的具体内容

**第三步：收集研究结果**
等待所有 researcher 完成，收集每个 researcher 返回的研究结果。

**第四步：输出结构化报告**
将所有研究结果综合为以下 JSON 格式输出（必须用 ```json 包裹）：

```json
{{
  "title": "研究报告: {topic} - YYYY-MM-DD",
  "blocks": [
    {{"type": "paragraph", "content": "研究时间: YYYY-MM-DD HH:MM:SS"}},
    {{"type": "heading_1", "content": "执行摘要"}},
    {{"type": "paragraph", "content": "综合所有研究结果的简要摘要（100-200字）"}},
    {{"type": "heading_1", "content": "研究详情"}},
    {{"type": "heading_2", "content": "子课题 1 标题"}},
    {{"type": "paragraph", "content": "子课题 1 的研究内容..."}},
    {{"type": "bulleted_list", "items": ["要点1", "要点2", "要点3"]}},
    {{"type": "heading_2", "content": "子课题 2 标题"}},
    {{"type": "paragraph", "content": "子课题 2 的研究内容..."}},
    {{"type": "heading_1", "content": "参考来源"}},
    {{"type": "bulleted_list", "items": ["来源1: URL", "来源2: URL"]}}
  ]
}}
```

**支持的块类型:**
- heading_1, heading_2, heading_3: 标题（content 字段）
- paragraph: 段落（content 字段）
- bulleted_list: 无序列表（items 字段，字符串数组）
- numbered_list: 有序列表（items 字段，字符串数组）
- code: 代码块（content 和 language 字段）
- divider: 分割线（无额外字段）
- to_do: 待办事项（content 和 checked 字段）

**重要:**
- 并行派发 researcher，不是串行
- 每个 researcher 负责不同的子课题
- 最终必须输出上述 JSON 格式，这是你的最后一步
- JSON 必须用 ```json 代码块包裹
"""


def get_lead_agent_prompt(topic: str) -> str:
    return LEAD_AGENT_PROMPT.format(topic=topic)
```

**Step 2: Commit**

```bash
git add app/agents/deepresearch/prompts/lead_agent.py
git commit -m "refactor: 更新 Lead Agent prompt 输出结构化 JSON"
```

---

## Task 5: 更新 DeepResearch Agent 主逻辑

**Files:**
- Modify: `app/agents/deepresearch/agent.py`
- Delete: `app/agents/deepresearch/prompts/notion_writer.py`

**Step 1: 更新 agent.py**

将文件内容替换为：

```python
from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions

from app.agents.base import BaseAgent
from app.agents.deepresearch.config import (
    MODEL,
    NOTION_TOKEN,
    NOTION_PARENT_PAGE_ID,
    MAX_TURNS,
    MCP_SERVERS,
    SEARCH_DEPTH,
    MAX_RESULTS,
)
from app.agents.deepresearch.prompts.lead_agent import get_lead_agent_prompt
from app.agents.deepresearch.prompts.researcher import get_researcher_prompt
from app.services.notion import (
    NotionService,
    parse_agent_output,
    blocks_to_notion_format,
    NotionWriteError,
)


class DeepResearchAgent(BaseAgent):
    """深度研究 Agent - 多 Agent 协作完成研究任务"""

    MODULE_NAME = "deepresearch"

    def get_prompt(self, topic: str) -> str:
        return get_lead_agent_prompt(topic)

    def get_options(self) -> ClaudeAgentOptions:
        # 构建 subagent 定义（只保留 researcher）
        agents = {
            "researcher": AgentDefinition(
                description="使用 Tavily 搜索指定子课题，返回研究结果",
                prompt=get_researcher_prompt(
                    search_depth=SEARCH_DEPTH,
                    max_results=MAX_RESULTS,
                ),
                tools=["mcp__tavily__tavily-search"],
                model="haiku",
            ),
        }

        return ClaudeAgentOptions(
            model=MODEL,
            max_turns=MAX_TURNS,
            permission_mode="bypassPermissions",
            mcp_servers=MCP_SERVERS,
            agents=agents,
            allowed_tools=["Task"],
        )

    def get_input_data(self, topic: str) -> dict:
        return {"topic": topic}

    def get_final_output(self, messages: list) -> str:
        """从消息列表中提取最终输出"""
        # 倒序遍历，找到最后一个包含 JSON 的 assistant 消息
        for msg in reversed(messages):
            if hasattr(msg, "content"):
                content = msg.content
                if isinstance(content, list):
                    for block in content:
                        if hasattr(block, "text") and "```json" in block.text:
                            return block.text
                elif isinstance(content, str) and "```json" in content:
                    return content
        return ""


async def run_deepresearch_agent(topic: str) -> None:
    """执行 DeepResearch Agent"""
    from claude_agent_sdk import query, AssistantMessage, TextBlock

    agent = DeepResearchAgent()
    prompt = agent.get_prompt(topic)
    options = agent.get_options()

    # 收集所有消息
    messages = []
    final_text = ""

    async for message in query(prompt=prompt, options=options):
        messages.append(message)
        if isinstance(message, AssistantMessage):
            for block in getattr(message, "content", []):
                if isinstance(block, TextBlock):
                    text = getattr(block, "text", "")
                    if "```json" in text:
                        final_text = text

    # 解析 Agent 输出并写入 Notion
    if final_text:
        try:
            parsed = parse_agent_output(final_text)
            notion_blocks = blocks_to_notion_format(parsed["blocks"])

            notion_service = NotionService(NOTION_TOKEN)
            notion_service.create_page(
                parent_page_id=NOTION_PARENT_PAGE_ID,
                title=parsed["title"],
                blocks=notion_blocks,
            )
        except (ValueError, NotionWriteError) as e:
            import logging
            logging.getLogger(__name__).error(f"Notion 写入失败: {e}")
            raise
```

**Step 2: 删除 notion_writer.py**

```bash
rm app/agents/deepresearch/prompts/notion_writer.py
```

**Step 3: Commit**

```bash
git add app/agents/deepresearch/agent.py
git rm app/agents/deepresearch/prompts/notion_writer.py
git commit -m "refactor: DeepResearch 使用 SDK 写入 Notion，移除 notion-writer SubAgent"
```

---

## Task 6: 更新 NewProjectAnalyse Agent

**Files:**
- Modify: `app/agents/newprojectanalyse/agent.py`

**Step 1: 更新 agent.py**

将文件内容替换为：

```python
from datetime import datetime

from claude_agent_sdk import ClaudeAgentOptions

from app.agents.base import BaseAgent
from app.agents.newprojectanalyse.config import (
    MODEL,
    NOTION_TOKEN,
    NOTION_PARENT_PAGE_ID,
    MAX_TURNS,
    MCP_SERVERS,
)
from app.services.notion import (
    NotionService,
    parse_agent_output,
    blocks_to_notion_format,
    NotionWriteError,
)


class NewProjectAnalyseAgent(BaseAgent):
    """新项目分析 Agent - 抓取项目 URL 内容并创建 Notion 页面"""

    MODULE_NAME = "newprojectanalyse"

    def get_prompt(self, url: str) -> str:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""
请完成以下任务：

1. 使用 mcp__firecrawl__firecrawl_scrape 工具抓取这个 URL 的内容：{url}

2. 为抓取的内容生成一个简洁的中文标题（10字以内）

3. 将内容总结并输出为以下 JSON 格式（必须用 ```json 包裹）：

```json
{{
  "title": "生成的中文标题",
  "blocks": [
    {{"type": "paragraph", "content": "任务时间: {current_time}"}},
    {{"type": "paragraph", "content": "原始链接: {url}"}},
    {{"type": "divider"}},
    {{"type": "heading_1", "content": "项目概述"}},
    {{"type": "paragraph", "content": "项目简介...（如果是 GitHub 项目，包含 star/fork/最后更新信息）"}},
    {{"type": "heading_1", "content": "核心要点"}},
    {{"type": "bulleted_list", "items": ["要点1", "要点2", "要点3", "要点4", "要点5"]}},
    {{"type": "heading_1", "content": "详细总结"}},
    {{"type": "paragraph", "content": "200-300字的详细总结..."}},
    {{"type": "heading_1", "content": "核心逻辑思维导图"}},
    {{"type": "bulleted_list", "items": ["主要模块1", "  - 子模块1.1", "  - 子模块1.2", "主要模块2", "  - 子模块2.1"]}}
  ]
}}
```

**支持的块类型:**
- heading_1, heading_2, heading_3: 标题（content 字段）
- paragraph: 段落（content 字段）
- bulleted_list: 无序列表（items 字段，字符串数组）
- numbered_list: 有序列表（items 字段，字符串数组）
- code: 代码块（content 和 language 字段）
- divider: 分割线（无额外字段）
- to_do: 待办事项（content 和 checked 字段）

**重要:**
- 最终必须输出上述 JSON 格式
- JSON 必须用 ```json 代码块包裹
- 确保 JSON 格式正确，可以被解析
"""

    def get_options(self) -> ClaudeAgentOptions:
        return ClaudeAgentOptions(
            model=MODEL,
            max_turns=MAX_TURNS,
            permission_mode="bypassPermissions",
            mcp_servers=MCP_SERVERS,
        )

    def get_input_data(self, url: str) -> dict:
        return {"url": url}


async def run_newprojectanalyse_agent(url: str) -> None:
    """执行 newprojectanalyse Agent"""
    from claude_agent_sdk import query, AssistantMessage, TextBlock

    agent = NewProjectAnalyseAgent()
    prompt = agent.get_prompt(url)
    options = agent.get_options()

    # 收集最终输出
    final_text = ""

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in getattr(message, "content", []):
                if isinstance(block, TextBlock):
                    text = getattr(block, "text", "")
                    if "```json" in text:
                        final_text = text

    # 解析 Agent 输出并写入 Notion
    if final_text:
        try:
            parsed = parse_agent_output(final_text)
            notion_blocks = blocks_to_notion_format(parsed["blocks"])

            notion_service = NotionService(NOTION_TOKEN)
            notion_service.create_page(
                parent_page_id=NOTION_PARENT_PAGE_ID,
                title=parsed["title"],
                blocks=notion_blocks,
            )
        except (ValueError, NotionWriteError) as e:
            import logging
            logging.getLogger(__name__).error(f"Notion 写入失败: {e}")
            raise
```

**Step 2: Commit**

```bash
git add app/agents/newprojectanalyse/agent.py
git commit -m "refactor: NewProjectAnalyse 使用 SDK 写入 Notion"
```

---

## Task 7: 更新 BaseAgent 以支持最终输出处理

**Files:**
- Modify: `app/agents/base.py`

**Step 1: 更新 base.py run 方法**

在 `BaseAgent` 类中添加 `process_final_output` 方法，并修改 `run` 方法以支持后处理：

在类中添加方法（在 `get_input_data` 方法之后）：

```python
    async def process_final_output(self, final_text: str, **kwargs) -> None:
        """
        处理 Agent 的最终输出（子类可覆盖）

        Args:
            final_text: Agent 输出的文本
            **kwargs: 传递给 run() 的参数
        """
        pass
```

修改 `run` 方法，在 `try` 块内、`async for` 循环之后、`logger.finish` 之前添加：

```python
            # 收集最终文本输出
            final_text = ""
            for msg in reversed(messages_collected):
                if isinstance(msg, AssistantMessage):
                    for block in getattr(msg, "content", []):
                        if isinstance(block, TextBlock):
                            text = getattr(block, "text", "")
                            if text:
                                final_text = text
                                break
                    if final_text:
                        break

            # 处理最终输出
            await self.process_final_output(final_text, **kwargs)
```

并在循环开始前添加 `messages_collected = []`，循环内添加 `messages_collected.append(message)`。

**注意：** 这个 Task 比较复杂，需要仔细阅读现有的 `run` 方法并做精确修改。完整的修改后的 `run` 方法如下：

```python
    async def run(self, **kwargs) -> None:
        """
        执行 Agent 任务

        Args:
            **kwargs: 传递给 get_prompt() 的参数
        """
        # 生成任务 ID
        task_id = task_registry.generate_id(self.MODULE_NAME)

        # 创建任务日志记录器
        input_data = self.get_input_data(**kwargs)
        logger = TaskLogger(task_id, input_data)

        prompt = self.get_prompt(**kwargs)
        options = self.get_options()

        # 记录用户 Prompt
        logger.log_user_prompt(prompt)

        tool_start_times: Dict[str, float] = {}  # tool_use_id -> start_time
        num_turns = 0
        cost_usd = 0.0
        messages_collected = []  # 收集所有消息

        try:
            async for message in query(prompt=prompt, options=options):
                messages_collected.append(message)

                if isinstance(message, AssistantMessage):
                    # 新的 Turn 开始
                    logger.log_turn_start()

                    # AssistantMessage.content 直接是 blocks 列表
                    blocks = getattr(message, "content", [])
                    for block in blocks:
                        if isinstance(block, ThinkingBlock):
                            # 记录思考过程
                            thinking_text = getattr(block, "thinking", "")
                            if thinking_text:
                                logger.log_thinking(thinking_text)

                        elif isinstance(block, TextBlock):
                            # 记录文本回复
                            text = getattr(block, "text", "")
                            if text:
                                logger.log_text(text)

                        elif isinstance(block, ToolUseBlock):
                            # 记录工具调用
                            tool_id = getattr(block, "id", "")
                            tool_start_times[tool_id] = time.time()
                            tool_name = getattr(block, "name", "unknown")
                            tool_input = getattr(block, "input", {})
                            logger.log_tool_call(tool_name, tool_id, tool_input)

                elif isinstance(message, UserMessage):
                    # 工具结果在 UserMessage 中
                    # UserMessage.content 可能是 str 或 list
                    msg_content = getattr(message, "content", None)
                    if isinstance(msg_content, list):
                        for block in msg_content:
                            if isinstance(block, ToolResultBlock):
                                tool_id = getattr(block, "tool_use_id", "")
                                start_time = tool_start_times.get(tool_id, 0)
                                duration = time.time() - start_time if start_time else 0
                                is_error = getattr(block, "is_error", False)
                                content = getattr(block, "content", "")
                                logger.log_tool_result(tool_id, content, is_error, duration)

                elif isinstance(message, ResultMessage):
                    cost_usd = getattr(message, "total_cost_usd", 0) or 0
                    num_turns = getattr(message, "num_turns", 0)

            # 收集最终文本输出（查找包含 JSON 的输出）
            final_text = ""
            for msg in reversed(messages_collected):
                if isinstance(msg, AssistantMessage):
                    for block in getattr(msg, "content", []):
                        if isinstance(block, TextBlock):
                            text = getattr(block, "text", "")
                            if text and "```json" in text:
                                final_text = text
                                break
                    if final_text:
                        break

            # 处理最终输出
            if final_text:
                await self.process_final_output(final_text, **kwargs)

            logger.finish(success=True, num_turns=num_turns, cost_usd=cost_usd)

        except Exception as e:
            logger.log_error(e)
            logger.finish(success=False, error=str(e), num_turns=num_turns, cost_usd=cost_usd)
            raise
```

**Step 2: Commit**

```bash
git add app/agents/base.py
git commit -m "refactor: BaseAgent 添加 process_final_output 钩子"
```

---

## Task 8: 重构 Agent 使用 BaseAgent 钩子

**Files:**
- Modify: `app/agents/deepresearch/agent.py`
- Modify: `app/agents/newprojectanalyse/agent.py`

**Step 1: 重构 deepresearch/agent.py**

将文件内容替换为（使用 `process_final_output` 钩子）：

```python
from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions

from app.agents.base import BaseAgent
from app.agents.deepresearch.config import (
    MODEL,
    NOTION_TOKEN,
    NOTION_PARENT_PAGE_ID,
    MAX_TURNS,
    MCP_SERVERS,
    SEARCH_DEPTH,
    MAX_RESULTS,
)
from app.agents.deepresearch.prompts.lead_agent import get_lead_agent_prompt
from app.agents.deepresearch.prompts.researcher import get_researcher_prompt
from app.services.notion import (
    NotionService,
    parse_agent_output,
    blocks_to_notion_format,
    NotionWriteError,
)


class DeepResearchAgent(BaseAgent):
    """深度研究 Agent - 多 Agent 协作完成研究任务"""

    MODULE_NAME = "deepresearch"

    def get_prompt(self, topic: str) -> str:
        return get_lead_agent_prompt(topic)

    def get_options(self) -> ClaudeAgentOptions:
        # 构建 subagent 定义（只保留 researcher）
        agents = {
            "researcher": AgentDefinition(
                description="使用 Tavily 搜索指定子课题，返回研究结果",
                prompt=get_researcher_prompt(
                    search_depth=SEARCH_DEPTH,
                    max_results=MAX_RESULTS,
                ),
                tools=["mcp__tavily__tavily-search"],
                model="haiku",
            ),
        }

        return ClaudeAgentOptions(
            model=MODEL,
            max_turns=MAX_TURNS,
            permission_mode="bypassPermissions",
            mcp_servers=MCP_SERVERS,
            agents=agents,
            allowed_tools=["Task"],
        )

    def get_input_data(self, topic: str) -> dict:
        return {"topic": topic}

    async def process_final_output(self, final_text: str, **kwargs) -> None:
        """处理最终输出，写入 Notion"""
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


async def run_deepresearch_agent(topic: str) -> None:
    """执行 DeepResearch Agent"""
    agent = DeepResearchAgent()
    await agent.run(topic=topic)
```

**Step 2: 重构 newprojectanalyse/agent.py**

将文件内容替换为：

```python
from datetime import datetime

from claude_agent_sdk import ClaudeAgentOptions

from app.agents.base import BaseAgent
from app.agents.newprojectanalyse.config import (
    MODEL,
    NOTION_TOKEN,
    NOTION_PARENT_PAGE_ID,
    MAX_TURNS,
    MCP_SERVERS,
)
from app.services.notion import (
    NotionService,
    parse_agent_output,
    blocks_to_notion_format,
)


class NewProjectAnalyseAgent(BaseAgent):
    """新项目分析 Agent - 抓取项目 URL 内容并创建 Notion 页面"""

    MODULE_NAME = "newprojectanalyse"

    def get_prompt(self, url: str) -> str:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""
请完成以下任务：

1. 使用 mcp__firecrawl__firecrawl_scrape 工具抓取这个 URL 的内容：{url}

2. 为抓取的内容生成一个简洁的中文标题（10字以内）

3. 将内容总结并输出为以下 JSON 格式（必须用 ```json 包裹）：

```json
{{{{
  "title": "生成的中文标题",
  "blocks": [
    {{{{"type": "paragraph", "content": "任务时间: {current_time}"}}}},
    {{{{"type": "paragraph", "content": "原始链接: {url}"}}}},
    {{{{"type": "divider"}}}},
    {{{{"type": "heading_1", "content": "项目概述"}}}},
    {{{{"type": "paragraph", "content": "项目简介...（如果是 GitHub 项目，包含 star/fork/最后更新信息）"}}}},
    {{{{"type": "heading_1", "content": "核心要点"}}}},
    {{{{"type": "bulleted_list", "items": ["要点1", "要点2", "要点3", "要点4", "要点5"]}}}},
    {{{{"type": "heading_1", "content": "详细总结"}}}},
    {{{{"type": "paragraph", "content": "200-300字的详细总结..."}}}},
    {{{{"type": "heading_1", "content": "核心逻辑思维导图"}}}},
    {{{{"type": "bulleted_list", "items": ["主要模块1", "  - 子模块1.1", "  - 子模块1.2", "主要模块2", "  - 子模块2.1"]}}}}
  ]
}}}}
```

**支持的块类型:**
- heading_1, heading_2, heading_3: 标题（content 字段）
- paragraph: 段落（content 字段）
- bulleted_list: 无序列表（items 字段，字符串数组）
- numbered_list: 有序列表（items 字段，字符串数组）
- code: 代码块（content 和 language 字段）
- divider: 分割线（无额外字段）
- to_do: 待办事项（content 和 checked 字段）

**重要:**
- 最终必须输出上述 JSON 格式
- JSON 必须用 ```json 代码块包裹
- 确保 JSON 格式正确，可以被解析
"""

    def get_options(self) -> ClaudeAgentOptions:
        return ClaudeAgentOptions(
            model=MODEL,
            max_turns=MAX_TURNS,
            permission_mode="bypassPermissions",
            mcp_servers=MCP_SERVERS,
        )

    def get_input_data(self, url: str) -> dict:
        return {{"url": url}}

    async def process_final_output(self, final_text: str, **kwargs) -> None:
        """处理最终输出，写入 Notion"""
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

**注意:** 上面的 f-string 中 JSON 示例需要使用四重大括号 `{{{{` 来转义，确保最终输出正确的 `{{`。

**Step 3: Commit**

```bash
git add app/agents/deepresearch/agent.py app/agents/newprojectanalyse/agent.py
git commit -m "refactor: Agent 使用 BaseAgent.process_final_output 钩子"
```

---

## Task 9: 最终验证

**Step 1: 检查语法错误**

```bash
cd /Users/nick/Syncthing/Develop/AI/claude-code-agent-sdk/.worktrees/notion-sdk-migration
source .venv/bin/activate
python -m py_compile app/services/notion.py
python -m py_compile app/agents/deepresearch/agent.py
python -m py_compile app/agents/newprojectanalyse/agent.py
python -m py_compile app/agents/base.py
python -m py_compile app/config.py
```

Expected: 无输出（无语法错误）

**Step 2: 检查导入**

```bash
python -c "from app.services.notion import NotionService, BlockBuilder, parse_agent_output, blocks_to_notion_format"
python -c "from app.agents.deepresearch.agent import DeepResearchAgent"
python -c "from app.agents.newprojectanalyse.agent import NewProjectAnalyseAgent"
```

Expected: 无错误

**Step 3: 最终 Commit（如有遗漏修改）**

```bash
git status
# 如有未提交的修改，提交它们
```

---

## 完成总结

实现计划包含 9 个任务：

1. 添加 notion-client 依赖
2. 创建 Notion 服务模块
3. 更新配置系统
4. 更新 DeepResearch Lead Agent Prompt
5. 更新 DeepResearch Agent 主逻辑（移除 notion-writer SubAgent）
6. 更新 NewProjectAnalyse Agent
7. 更新 BaseAgent 以支持最终输出处理
8. 重构 Agent 使用 BaseAgent 钩子
9. 最终验证

每个任务包含具体的文件修改、完整代码和 commit 命令。
