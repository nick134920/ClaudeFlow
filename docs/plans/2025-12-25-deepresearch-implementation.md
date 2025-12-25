# DeepResearch Agent 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现多 Agent 深度研究系统，使用 Tavily MCP 搜索，结果保存到 Notion 子页面。

**Architecture:** Lead Agent 协调任务分解，并行派发 Researcher subagent 使用 Tavily 搜索，最后 NotionWriter 综合结果创建 Notion 页面。

**Tech Stack:** Python, Claude Agent SDK, Tavily MCP, Notion MCP, FastAPI

---

## Task 1: 创建模块目录结构

**Files:**
- Create: `app/agents/deepresearch/__init__.py`
- Create: `app/agents/deepresearch/prompts/__init__.py`
- Create: `app/agents/deepresearch/files/research_notes/.gitkeep`

**Step 1: 创建目录结构**

```bash
mkdir -p app/agents/deepresearch/prompts
mkdir -p app/agents/deepresearch/files/research_notes
```

**Step 2: 创建 `__init__.py` 文件**

文件 `app/agents/deepresearch/__init__.py`:
```python
# DeepResearch Agent 模块
```

文件 `app/agents/deepresearch/prompts/__init__.py`:
```python
# DeepResearch Prompts
```

**Step 3: 创建 `.gitkeep` 文件**

```bash
touch app/agents/deepresearch/files/research_notes/.gitkeep
```

**Step 4: 提交**

```bash
git add app/agents/deepresearch/
git commit -m "feat(deepresearch): 创建模块目录结构"
```

---

## Task 2: 创建配置模块

**Files:**
- Create: `app/agents/deepresearch/config.py`
- Modify: `config.yaml.example`

**Step 1: 创建 `config.py`**

文件 `app/agents/deepresearch/config.py`:
```python
from pathlib import Path
from app.config import get_agent_config

_config = get_agent_config("deepresearch")

# 基础配置
MODEL: str = _config.get("model", "claude-sonnet-4-20250514")
NOTION_PARENT_PAGE_ID: str = _config.get("notion_parent_page_id", "")
MAX_TURNS: int = _config.get("max_turns", 20)

# Tavily 配置
TAVILY_CONFIG: dict = _config.get("tavily", {})
SEARCH_DEPTH: str = TAVILY_CONFIG.get("search_depth", "advanced")
MAX_RESULTS: int = TAVILY_CONFIG.get("max_results", 10)
INCLUDE_IMAGES: bool = TAVILY_CONFIG.get("include_images", False)

# MCP 服务器配置
MCP_SERVERS: dict = _config.get("mcp_servers", {})

# 文件路径
BASE_DIR = Path(__file__).resolve().parent
RESEARCH_NOTES_DIR = BASE_DIR / "files" / "research_notes"
```

**Step 2: 更新 `config.yaml.example`**

在文件末尾追加:
```yaml

# deepresearch agent 配置
deepresearch:
  model: claude-sonnet-4-20250514
  notion_parent_page_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  max_turns: 20
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
    notion:
      type: stdio
      command: npx
      args: ["-y", "@notionhq/notion-mcp-server"]
      env:
        NOTION_TOKEN: your-notion-token
```

**Step 3: 提交**

```bash
git add app/agents/deepresearch/config.py config.yaml.example
git commit -m "feat(deepresearch): 添加配置模块"
```

---

## Task 3: 创建 Lead Agent Prompt

**Files:**
- Create: `app/agents/deepresearch/prompts/lead_agent.py`

**Step 1: 创建 Lead Agent Prompt**

文件 `app/agents/deepresearch/prompts/lead_agent.py`:
```python
LEAD_AGENT_PROMPT = """你是一个研究协调者，负责协调多 Agent 研究任务。

**研究主题:** {topic}

**关键规则:**
1. 你只能使用 Task 工具派发 subagent，不能自己研究或写报告
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

**第三步：等待研究完成**
等待所有 researcher 完成工作。

**第四步：派发 NotionWriter**
使用 Task 工具派发 notion-writer subagent：
- subagent_type: "notion-writer"
- description: "综合研究结果创建 Notion 页面"
- prompt: "读取 files/research_notes/ 目录下的所有研究笔记，综合后在 Notion 创建子页面。研究主题: {topic}"

**第五步：确认完成**
告知用户研究完成，Notion 页面已创建。

**重要:**
- 并行派发 researcher，不是串行
- 每个 researcher 负责不同的子课题
- 等所有 researcher 完成后才派发 notion-writer
"""


def get_lead_agent_prompt(topic: str) -> str:
    return LEAD_AGENT_PROMPT.format(topic=topic)
```

**Step 2: 提交**

```bash
git add app/agents/deepresearch/prompts/lead_agent.py
git commit -m "feat(deepresearch): 添加 Lead Agent prompt"
```

---

## Task 4: 创建 Researcher Prompt

**Files:**
- Create: `app/agents/deepresearch/prompts/researcher.py`

**Step 1: 创建 Researcher Prompt**

文件 `app/agents/deepresearch/prompts/researcher.py`:
```python
RESEARCHER_PROMPT = """你是一个专业研究员，负责深度研究指定的子课题。

**Tavily 搜索参数:**
- search_depth: {search_depth}
- max_results: {max_results}

**工作流程:**

1. 使用 mcp__tavily__tavily-search 工具搜索相关信息
   - 构造精准的搜索查询
   - 使用配置的搜索参数

2. 分析搜索结果
   - 提取关键发现
   - 记录来源 URL
   - 总结重要观点

3. 使用 Write 工具将研究结果保存到文件
   - 文件路径: {research_notes_dir}/{{subtopic}}_{{timestamp}}.md
   - 使用当前时间戳命名文件

**输出格式:**

```markdown
# {{子课题标题}}

## 研究时间
{{YYYY-MM-DD HH:MM:SS}}

## 关键发现
- 发现 1
- 发现 2
- ...

## 详细内容
{{详细的研究内容}}

## 来源
- [标题1](URL1)
- [标题2](URL2)
```

**重要:**
- 专注于分配给你的子课题
- 确保记录所有来源 URL
- 内容要详实有价值
"""


def get_researcher_prompt(search_depth: str, max_results: int, research_notes_dir: str) -> str:
    return RESEARCHER_PROMPT.format(
        search_depth=search_depth,
        max_results=max_results,
        research_notes_dir=research_notes_dir,
    )
```

**Step 2: 提交**

```bash
git add app/agents/deepresearch/prompts/researcher.py
git commit -m "feat(deepresearch): 添加 Researcher prompt"
```

---

## Task 5: 创建 NotionWriter Prompt

**Files:**
- Create: `app/agents/deepresearch/prompts/notion_writer.py`

**Step 1: 创建 NotionWriter Prompt**

文件 `app/agents/deepresearch/prompts/notion_writer.py`:
```python
NOTION_WRITER_PROMPT = """你是一个报告编写专家，负责将研究笔记综合成 Notion 页面。

**Notion 父页面 ID:** {notion_parent_page_id}
**研究笔记目录:** {research_notes_dir}

**工作流程:**

1. 使用 Glob 工具列出 {research_notes_dir}/*.md 的所有文件

2. 使用 Read 工具读取每个研究笔记文件

3. 综合所有研究内容，生成结构化报告

4. 使用 mcp__notion__API-post-page 工具创建 Notion 子页面

**Notion 页面结构:**

```json
{{
  "parent": {{ "page_id": "{notion_parent_page_id}" }},
  "properties": {{
    "title": [{{ "text": {{ "content": "研究报告: {{主题}} - {{日期}}" }} }}]
  }},
  "children": [
    // 时间和来源信息
    {{ "type": "paragraph", "paragraph": {{ "rich_text": [{{ "type": "text", "text": {{ "content": "研究时间: {{时间}}" }} }}] }} }},

    // 执行摘要
    {{ "type": "heading_1", "heading_1": {{ "rich_text": [{{ "type": "text", "text": {{ "content": "执行摘要" }} }}] }} }},
    {{ "type": "paragraph", "paragraph": {{ "rich_text": [{{ "type": "text", "text": {{ "content": "{{摘要内容}}" }} }}] }} }},

    // 各子课题详情
    {{ "type": "heading_1", "heading_1": {{ "rich_text": [{{ "type": "text", "text": {{ "content": "研究详情" }} }}] }} }},
    {{ "type": "heading_2", "heading_2": {{ "rich_text": [{{ "type": "text", "text": {{ "content": "子课题 1" }} }}] }} }},
    // ... 子课题内容

    // 来源列表
    {{ "type": "heading_1", "heading_1": {{ "rich_text": [{{ "type": "text", "text": {{ "content": "参考来源" }} }}] }} }},
    {{ "type": "bulleted_list_item", "bulleted_list_item": {{ "rich_text": [{{ "type": "text", "text": {{ "content": "来源 1", "link": {{ "url": "URL1" }} }} }}] }} }}
  ]
}}
```

**重要:**
- children 参数必须是对象数组
- 不要使用 icon 参数
- 合并所有研究笔记的来源到参考来源部分
- 生成简洁有价值的执行摘要
"""


def get_notion_writer_prompt(notion_parent_page_id: str, research_notes_dir: str) -> str:
    return NOTION_WRITER_PROMPT.format(
        notion_parent_page_id=notion_parent_page_id,
        research_notes_dir=research_notes_dir,
    )
```

**Step 2: 提交**

```bash
git add app/agents/deepresearch/prompts/notion_writer.py
git commit -m "feat(deepresearch): 添加 NotionWriter prompt"
```

---

## Task 6: 创建 Agent 主入口

**Files:**
- Create: `app/agents/deepresearch/agent.py`

**Step 1: 创建 Agent 类**

文件 `app/agents/deepresearch/agent.py`:
```python
from datetime import datetime

from claude_agent_sdk import ClaudeAgentOptions

from app.agents.base import BaseAgent
from app.agents.deepresearch.config import (
    MODEL,
    NOTION_PARENT_PAGE_ID,
    MAX_TURNS,
    MCP_SERVERS,
    SEARCH_DEPTH,
    MAX_RESULTS,
    RESEARCH_NOTES_DIR,
)
from app.agents.deepresearch.prompts.lead_agent import get_lead_agent_prompt
from app.agents.deepresearch.prompts.researcher import get_researcher_prompt
from app.agents.deepresearch.prompts.notion_writer import get_notion_writer_prompt


class DeepResearchAgent(BaseAgent):
    """深度研究 Agent - 多 Agent 协作完成研究任务"""

    MODULE_NAME = "deepresearch"

    def __init__(self):
        super().__init__()
        # 确保研究笔记目录存在
        RESEARCH_NOTES_DIR.mkdir(parents=True, exist_ok=True)

    def get_prompt(self, topic: str) -> str:
        return get_lead_agent_prompt(topic)

    def get_options(self) -> ClaudeAgentOptions:
        # 构建 subagent 定义
        agents = {
            "researcher": {
                "description": "使用 Tavily 搜索指定子课题，将结果写入 research_notes/",
                "prompt": get_researcher_prompt(
                    search_depth=SEARCH_DEPTH,
                    max_results=MAX_RESULTS,
                    research_notes_dir=str(RESEARCH_NOTES_DIR),
                ),
                "tools": ["mcp__tavily__tavily-search", "Write"],
                "model": "haiku",
            },
            "notion-writer": {
                "description": "读取研究笔记，综合后创建 Notion 子页面",
                "prompt": get_notion_writer_prompt(
                    notion_parent_page_id=NOTION_PARENT_PAGE_ID,
                    research_notes_dir=str(RESEARCH_NOTES_DIR),
                ),
                "tools": [
                    "Read",
                    "Glob",
                    "mcp__notion__API-post-page",
                    "mcp__notion__API-patch-block-children",
                ],
                "model": "sonnet",
            },
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


async def run_deepresearch_agent(topic: str) -> None:
    """执行 DeepResearch Agent"""
    agent = DeepResearchAgent()
    await agent.run(topic=topic)
```

**Step 2: 提交**

```bash
git add app/agents/deepresearch/agent.py
git commit -m "feat(deepresearch): 添加 Agent 主入口"
```

---

## Task 7: 添加 API 请求模型

**Files:**
- Modify: `app/api/models.py`

**Step 1: 添加 DeepResearchRequest 模型**

在 `app/api/models.py` 文件末尾追加:
```python


class DeepResearchRequest(BaseModel):
    """深度研究请求模型"""
    topic: str

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("研究主题至少需要 2 个字符")
        if len(v) > 500:
            raise ValueError("研究主题不能超过 500 个字符")
        return v
```

**Step 2: 提交**

```bash
git add app/api/models.py
git commit -m "feat(deepresearch): 添加 API 请求模型"
```

---

## Task 8: 添加 API 路由

**Files:**
- Modify: `app/api/routes.py`

**Step 1: 添加导入**

在 `app/api/routes.py` 文件顶部的导入部分追加:
```python
from app.api.models import NewProjectAnalyseRequest, TaskResponse, HealthCheckResponse, DeepResearchRequest
from app.agents.deepresearch.agent import run_deepresearch_agent
```

注意: 修改已有的 `from app.api.models import ...` 行，添加 `DeepResearchRequest`。

**Step 2: 添加路由端点**

在 `app/api/routes.py` 文件末尾追加:
```python


@router.post("/deepresearch", response_model=TaskResponse)
async def deepresearch(
    request: Request,
    body: DeepResearchRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Query(..., description="API Key"),
):
    """
    提交深度研究任务

    - 验证 API Key
    - 验证主题格式
    - 提交后台任务
    - 返回任务 ID
    """
    client_ip = get_client_ip(request)
    path = "/deepresearch"

    # 验证 API Key
    if api_key != API_KEY:
        request_logger.log(
            "WARNING", "POST", path, client_ip,
            status="rejected", extra={"reason": "invalid_api_key"}
        )
        return TaskResponse(success=False, message="Invalid API Key")

    # 生成任务 ID
    task_id = task_registry.generate_id("deepresearch")

    # 记录请求日志
    request_logger.log(
        "INFO", "POST", path, client_ip,
        task_id=task_id, status="accepted", extra={"topic": body.topic}
    )

    # 添加后台任务
    background_tasks.add_task(run_deepresearch_agent, body.topic)

    return TaskResponse(success=True, task_id=task_id)
```

**Step 3: 提交**

```bash
git add app/api/routes.py
git commit -m "feat(deepresearch): 添加 API 路由"
```

---

## Task 9: 最终验证

**Step 1: 检查语法**

```bash
python -m py_compile app/agents/deepresearch/config.py
python -m py_compile app/agents/deepresearch/agent.py
python -m py_compile app/agents/deepresearch/prompts/lead_agent.py
python -m py_compile app/agents/deepresearch/prompts/researcher.py
python -m py_compile app/agents/deepresearch/prompts/notion_writer.py
python -m py_compile app/api/routes.py
python -m py_compile app/api/models.py
```

预期: 无输出表示语法正确。

**Step 2: 检查导入**

```bash
cd /Users/nick/Syncthing/Develop/AI/claude-code-agent-sdk
python -c "from app.agents.deepresearch.agent import run_deepresearch_agent; print('Import OK')"
```

预期: `Import OK`

**Step 3: 提交最终状态**

如果有任何修复，提交:
```bash
git add -A
git commit -m "fix(deepresearch): 修复导入和语法问题"
```

---

## 任务清单总结

| Task | 描述 | 文件 |
|------|------|------|
| 1 | 创建模块目录结构 | `__init__.py`, `.gitkeep` |
| 2 | 创建配置模块 | `config.py`, `config.yaml.example` |
| 3 | 创建 Lead Agent Prompt | `prompts/lead_agent.py` |
| 4 | 创建 Researcher Prompt | `prompts/researcher.py` |
| 5 | 创建 NotionWriter Prompt | `prompts/notion_writer.py` |
| 6 | 创建 Agent 主入口 | `agent.py` |
| 7 | 添加 API 请求模型 | `models.py` |
| 8 | 添加 API 路由 | `routes.py` |
| 9 | 最终验证 | 语法和导入检查 |
