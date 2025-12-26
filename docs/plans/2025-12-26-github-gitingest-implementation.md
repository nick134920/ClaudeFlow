# GitHub gitingest 分析功能实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 NewProjectAnalyseAgent 增加 GitHub 仓库识别和 gitingest 深度分析功能

**Architecture:** 在代码层面预处理 URL，判断是否为 GitHub 仓库。如果是，调用 gitingest 获取仓库内容并注入到专用 Prompt；否则保持现有 firecrawl 流程。

**Tech Stack:** Python, gitingest, claude-agent-sdk

---

## Task 1: 添加 gitingest 依赖

**Files:**
- Modify: `requirements.txt`

**Step 1: 添加依赖**

在 `requirements.txt` 末尾添加：

```
gitingest
```

**Step 2: 安装依赖**

Run: `pip install gitingest`

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: 添加 gitingest 依赖"
```

---

## Task 2: 添加 GitHub URL 判断函数和 gitingest 调用函数

**Files:**
- Modify: `app/agents/newprojectanalyse/agent.py:1-18`

**Step 1: 添加导入和工具函数**

在文件顶部导入区域后，添加：

```python
import re


# GitHub 仓库 URL 排除模式
GITHUB_EXCLUDE_PATTERNS = [
    "node_modules/*", "vendor/*", ".venv/*", "venv/*",
    "dist/*", "build/*", ".git/*",
    "*.lock", "*.min.js", "*.min.css",
    "*.log", "*.pyc", "__pycache__/*"
]


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
        exclude_patterns=GITHUB_EXCLUDE_PATTERNS
    )
    return summary, tree, content
```

**Step 2: Commit**

```bash
git add app/agents/newprojectanalyse/agent.py
git commit -m "feat: 添加 GitHub URL 判断和 gitingest 调用函数"
```

---

## Task 3: 重命名现有 get_prompt 为 get_prompt_for_web

**Files:**
- Modify: `app/agents/newprojectanalyse/agent.py:25-86`

**Step 1: 重命名方法**

将 `def get_prompt(self, url: str) -> str:` 改为 `def get_prompt_for_web(self, url: str) -> str:`

同时更新 docstring：

```python
def get_prompt_for_web(self, url: str) -> str:
    """获取非 GitHub URL 的 Prompt（使用 firecrawl 抓取）"""
```

**Step 2: Commit**

```bash
git add app/agents/newprojectanalyse/agent.py
git commit -m "refactor: 重命名 get_prompt 为 get_prompt_for_web"
```

---

## Task 4: 添加 get_prompt_for_github 方法

**Files:**
- Modify: `app/agents/newprojectanalyse/agent.py`

**Step 1: 在 get_prompt_for_web 方法后添加新方法**

```python
def get_prompt_for_github(self, url: str, summary: str, tree: str, content: str) -> str:
    """获取 GitHub 仓库的 Prompt（使用 gitingest 内容）"""
    current_date = datetime.now().strftime("%Y%m%d")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""
请分析以下 GitHub 仓库：{url}

## 仓库信息（由 gitingest 获取）

### 概要
{summary}

### 目录结构
{tree}

### 源代码内容
{content}

## 任务

1. 从上方目录结构中提取 owner 和 repo，使用 GitHub API 获取项目统计信息：
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
    {{"type": "heading_1", "content": "项目结构"}},
    {{"type": "code", "content": "简化的目录树形结构，只保留关键目录和文件", "language": "text"}},
    {{"type": "paragraph", "content": "项目结构说明，解释主要目录的用途..."}},
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
- title 格式必须为: "项目名称-中文标题-{current_date}"
- 必须获取并显示 star/fork/最后提交时间，使用 callout 块展示
- 项目结构使用 code 块展示简化的目录树，后跟 paragraph 说明
- 部署说明从 README、Dockerfile、package.json 等文件中提取
- 任务时间必须放在内容最后
- 最终必须输出上述 JSON 格式
- JSON 必须用 ```json 代码块包裹
- 确保 JSON 格式正确，可以被解析
"""
```

**Step 2: Commit**

```bash
git add app/agents/newprojectanalyse/agent.py
git commit -m "feat: 添加 get_prompt_for_github 方法"
```

---

## Task 5: 添加 get_prompt 分发方法

**Files:**
- Modify: `app/agents/newprojectanalyse/agent.py`

**Step 1: 添加 get_prompt 方法作为分发器**

在 `get_prompt_for_github` 方法后添加：

```python
def get_prompt(self, url: str, github_content: tuple[str, str, str] | None = None) -> str:
    """
    获取 Agent 提示词

    Args:
        url: 目标 URL
        github_content: GitHub 仓库内容 (summary, tree, content)，仅当 URL 为 GitHub 仓库时传入

    Returns:
        str: 生成的 Prompt
    """
    if github_content is not None:
        summary, tree, content = github_content
        return self.get_prompt_for_github(url, summary, tree, content)
    else:
        return self.get_prompt_for_web(url)
```

**Step 2: Commit**

```bash
git add app/agents/newprojectanalyse/agent.py
git commit -m "feat: 添加 get_prompt 分发方法"
```

---

## Task 6: 重写 run 方法以支持 GitHub 预处理

**Files:**
- Modify: `app/agents/newprojectanalyse/agent.py`

**Step 1: 重写 run 方法**

在 `NewProjectAnalyseAgent` 类中重写 `run` 方法：

```python
async def run(self, **kwargs) -> None:
    """
    执行 Agent 任务（重写以支持 GitHub 仓库预处理）

    Args:
        **kwargs: 必须包含 url 参数
    """
    from app.core.logging import TaskLogger
    from app.core.task_registry import task_registry
    from claude_agent_sdk import (
        query,
        AssistantMessage,
        ResultMessage,
        ToolUseBlock,
        ToolResultBlock,
        UserMessage,
        TextBlock,
        ThinkingBlock,
    )
    import time

    url = kwargs.get("url")
    if not url:
        raise ValueError("url 参数是必需的")

    # 生成任务 ID
    task_id = task_registry.generate_id(self.MODULE_NAME)

    # 创建任务日志记录器
    input_data = self.get_input_data(**kwargs)
    logger = TaskLogger(task_id, input_data)

    # 预处理：判断是否为 GitHub 仓库
    github_content = None
    if is_github_repo_url(url):
        logger.info(f"检测到 GitHub 仓库 URL，使用 gitingest 获取内容...")
        try:
            github_content = await fetch_github_repo_content(url)
            logger.info(f"gitingest 获取成功")
        except Exception as e:
            logger.warning(f"gitingest 获取失败，回退到 firecrawl: {e}")
            github_content = None

    prompt = self.get_prompt(url, github_content)
    options = self.get_options()

    # 记录用户 Prompt
    logger.log_user_prompt(prompt)

    tool_start_times = {}
    num_turns = 0
    cost_usd = 0.0
    structured_output = None
    messages_collected = []

    try:
        async for message in query(prompt=prompt, options=options):
            messages_collected.append(message)
            if isinstance(message, AssistantMessage):
                logger.log_turn_start()
                blocks = getattr(message, "content", [])
                for block in blocks:
                    if isinstance(block, ThinkingBlock):
                        thinking_text = getattr(block, "thinking", "")
                        if thinking_text:
                            logger.log_thinking(thinking_text)
                    elif isinstance(block, TextBlock):
                        text = getattr(block, "text", "")
                        if text:
                            logger.log_text(text)
                    elif isinstance(block, ToolUseBlock):
                        tool_id = getattr(block, "id", "")
                        tool_start_times[tool_id] = time.time()
                        tool_name = getattr(block, "name", "unknown")
                        tool_input = getattr(block, "input", {})
                        logger.log_tool_call(tool_name, tool_id, tool_input)

            elif isinstance(message, UserMessage):
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
                structured_output = getattr(message, "structured_output", None)

        # 处理最终输出
        if structured_output is not None:
            await self.process_structured_output(structured_output, **kwargs)
        else:
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

            if final_text:
                await self.process_final_output(final_text, **kwargs)

        logger.finish(success=True, num_turns=num_turns, cost_usd=cost_usd)

    except Exception as e:
        logger.log_error(e)
        logger.finish(success=False, error=str(e), num_turns=num_turns, cost_usd=cost_usd)
```

**Step 2: Commit**

```bash
git add app/agents/newprojectanalyse/agent.py
git commit -m "feat: 重写 run 方法支持 GitHub 仓库预处理"
```

---

## Task 7: 验证和最终提交

**Step 1: 检查语法**

Run: `python -m py_compile app/agents/newprojectanalyse/agent.py`

Expected: 无输出表示成功

**Step 2: 最终 Commit（如有未提交的修改）**

```bash
git add -A
git commit -m "feat: 完成 GitHub gitingest 分析功能"
```

---

## 完整文件结构（供参考）

实现完成后，`agent.py` 的结构应为：

```
imports
    ├── datetime
    ├── re
    ├── claude_agent_sdk
    ├── app.agents.base
    ├── app.agents.newprojectanalyse.config
    └── app.services.notion

constants
    └── GITHUB_EXCLUDE_PATTERNS

functions
    ├── is_github_repo_url()
    └── fetch_github_repo_content()

class NewProjectAnalyseAgent(BaseAgent)
    ├── MODULE_NAME
    ├── get_prompt_for_web()      # 原 get_prompt，处理非 GitHub URL
    ├── get_prompt_for_github()   # 新增，处理 GitHub 仓库
    ├── get_prompt()              # 分发器
    ├── get_options()
    ├── get_input_data()
    ├── process_final_output()
    └── run()                     # 重写，支持 GitHub 预处理

function
    └── run_newprojectanalyse_agent()
```
