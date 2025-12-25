# DeepResearch Agent 设计文档

## 概述

基于 Claude Agent SDK Python 版本实现的多 Agent 深度研究系统。使用 Tavily MCP 进行网络搜索，将研究结果保存到 Notion 指定页面下的子页面。

## 目录结构

```
app/agents/deepresearch/
├── __init__.py
├── agent.py              # 主入口，DeepResearchAgent 类
├── config.py             # 从 config.yaml 读取配置
├── files/
│   └── research_notes/   # Researcher 输出的研究笔记
└── prompts/
    ├── __init__.py
    ├── lead_agent.py     # Lead Agent prompt
    ├── researcher.py     # Researcher subagent prompt
    └── notion_writer.py  # NotionWriter subagent prompt
```

## 配置扩展

在 `config.yaml` 中新增 `deepresearch` 配置节：

```yaml
deepresearch:
  model: claude-sonnet-4-20250514
  notion_parent_page_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  max_turns: 20
  tavily:
    search_depth: advanced      # basic | advanced
    max_results: 10
    include_images: false
  mcp_servers:
    tavily:
      type: stdio
      command: npx
      args: ["-y", "tavily-mcp@latest"]
      env:
        TAVILY_API_KEY: your-tavily-api-key
    notion:
      type: stdio
      command: npx
      args: ["-y", "@notionhq/notion-mcp-server"]
      env:
        NOTION_TOKEN: your-notion-token
```

## Agent 架构

### 工作流程

```
用户输入研究主题
       ↓
┌─────────────────────────────────────────┐
│  Lead Agent (协调者)                     │
│  - 分解主题为 2-4 个子课题                │
│  - 并行派发 Researcher subagent          │
│  - 等待所有研究完成后派发 NotionWriter    │
│  - Tools: Task (仅用于生成 subagent)      │
└─────────────────────────────────────────┘
       ↓ 并行生成
┌─────────────────┐  ┌─────────────────┐
│ Researcher #1   │  │ Researcher #2   │  ...
│ - 子课题 A      │  │ - 子课题 B      │
│ - Tavily 搜索   │  │ - Tavily 搜索   │
│ - 写入本地文件  │  │ - 写入本地文件  │
└─────────────────┘  └─────────────────┘
       ↓ 全部完成后
┌─────────────────────────────────────────┐
│  NotionWriter                            │
│  - 读取所有研究笔记                       │
│  - 综合生成结构化报告                     │
│  - 在 Notion 父页面下创建子页面           │
│  - Tools: Read, Glob, mcp__notion__*     │
└─────────────────────────────────────────┘
       ↓
Notion 子页面创建完成，返回页面链接
```

### Subagent 定义

```python
agents = {
    "researcher": {
        "description": "使用 Tavily 搜索指定子课题，将结果写入 research_notes/",
        "prompt": researcher_prompt,
        "tools": ["mcp__tavily__tavily-search", "Write"],
        "model": "haiku",
    },
    "notion-writer": {
        "description": "读取研究笔记，综合后创建 Notion 子页面",
        "prompt": notion_writer_prompt,
        "tools": ["Read", "Glob", "mcp__notion__API-post-page", "mcp__notion__API-patch-block-children"],
        "model": "sonnet",
    },
}
```

## Prompts 设计

### Lead Agent

- 角色：研究协调者，仅使用 Task 工具派发 subagent
- 关键规则：
  - 将用户主题分解为 2-4 个独立子课题
  - 并行派发多个 researcher（不是串行）
  - 等待所有 researcher 完成后，派发 notion-writer
  - 保持简洁，不自行研究或写报告

### Researcher

- 角色：专注单一子课题的深度研究
- 工具：`mcp__tavily__tavily-search`, `Write`
- 输出：将搜索结果写入 `files/research_notes/{topic}_{timestamp}.md`
- 包含：来源 URL、关键发现、引用摘要

### NotionWriter

- 角色：综合所有研究笔记，创建 Notion 页面
- 工具：`Read`, `Glob`, `mcp__notion__API-post-page`, `mcp__notion__API-patch-block-children`
- 输出结构：标题（研究主题 + 日期）→ 执行摘要 → 各子课题详情 → 来源列表
- 遵循现有 `newprojectanalyse` 的 Notion Block 规范

## API 接口

### 端点

```
POST /deepresearch
```

### 请求体

```python
class DeepResearchRequest(BaseModel):
    topic: str  # 研究主题
```

### 响应

```python
class TaskResponse(BaseModel):
    task_id: str
    status: str
```

## 代码实现

### agent.py

```python
class DeepResearchAgent(BaseAgent):
    MODULE_NAME = "deepresearch"

    def get_prompt(self, topic: str) -> str:
        return lead_agent_prompt.format(topic=topic, ...)

    def get_options(self) -> ClaudeAgentOptions:
        return ClaudeAgentOptions(
            model=MODEL,
            max_turns=MAX_TURNS,
            permission_mode="bypassPermissions",
            mcp_servers=MCP_SERVERS,
            agents=AGENTS,
            allowed_tools=["Task"],
        )

async def run_deepresearch_agent(topic: str) -> None:
    agent = DeepResearchAgent()
    await agent.run(topic=topic)
```

### config.py

```python
from app.config import get_agent_config

_config = get_agent_config("deepresearch")

MODEL: str = _config.get("model", "claude-sonnet-4-20250514")
NOTION_PARENT_PAGE_ID: str = _config.get("notion_parent_page_id", "")
MAX_TURNS: int = _config.get("max_turns", 20)

TAVILY_CONFIG: dict = _config.get("tavily", {})
SEARCH_DEPTH: str = TAVILY_CONFIG.get("search_depth", "advanced")
MAX_RESULTS: int = TAVILY_CONFIG.get("max_results", 10)

MCP_SERVERS: dict = _config.get("mcp_servers", {})
```

## 决策总结

| 决策项 | 选择 |
|--------|------|
| 位置 | `app/agents/deepresearch/` |
| 架构 | Lead → Researcher ×N → NotionWriter |
| Notion 保存 | 父页面下创建子页面 |
| 配置 | 扩展 `config.yaml` |
| Subagent 定义 | 代码定义（`prompts/` 目录）|
| API | `POST /deepresearch` |
