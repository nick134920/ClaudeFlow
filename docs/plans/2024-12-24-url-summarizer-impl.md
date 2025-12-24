# URL 总结服务实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一个 HTTP 服务，接收 URL 后异步抓取内容、总结并创建 Notion Page

**Architecture:** FastAPI 接收请求后立即返回，后台通过 Claude Agent SDK 调用 MCP Firecrawl 抓取内容，Claude 生成 Markdown 总结，最后通过 MCP Notion 创建 Page

**Tech Stack:** FastAPI, uvicorn, python-dotenv, claude-agent-sdk

---

### Task 1: 创建依赖文件

**Files:**
- Create: `requirements.txt`

**Step 1: 创建 requirements.txt**

```txt
fastapi
uvicorn
python-dotenv
claude-agent-sdk
```

**Step 2: Commit**

```bash
git add requirements.txt
git commit -m "feat: 添加项目依赖"
```

---

### Task 2: 创建配置文件模板

**Files:**
- Create: `.env.example`

**Step 1: 创建 .env.example**

```env
API_KEY=your-secret-key
NOTION_PARENT_PAGE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

**Step 2: 添加 .gitignore**

```gitignore
.env
__pycache__/
*.pyc
```

**Step 3: Commit**

```bash
git add .env.example .gitignore
git commit -m "feat: 添加配置模板和 gitignore"
```

---

### Task 3: 实现 Agent 模块

**Files:**
- Create: `agent.py`

**Step 1: 创建 agent.py**

```python
import asyncio
import os
from claude_agent_sdk import query, ClaudeAgentOptions

NOTION_PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID")


async def run_summarize_agent(url: str) -> None:
    """后台任务：抓取 URL 内容，总结并创建 Notion Page"""

    prompt = f"""
请完成以下任务：

1. 使用 Firecrawl 工具抓取这个 URL 的内容：{url}

2. 为抓取的内容生成一个简洁的中文标题（10字以内）

3. 将内容总结为 Markdown 格式，包含：
   - 核心要点（3-5 条）
   - 详细总结（200-300字）

4. 使用 Notion 工具在父页面 {NOTION_PARENT_PAGE_ID} 下创建一个新 Page：
   - 标题：生成的中文标题
   - 内容：Markdown 格式的总结
"""

    options = ClaudeAgentOptions(
        max_turns=15,
    )

    try:
        async for message in query(prompt=prompt, options=options):
            pass  # Agent 自主执行，无需处理输出
    except Exception as e:
        print(f"Agent 执行失败: {e}")
```

**Step 2: Commit**

```bash
git add agent.py
git commit -m "feat: 实现 Agent 模块"
```

---

### Task 4: 实现 FastAPI 服务

**Files:**
- Create: `main.py`

**Step 1: 创建 main.py**

```python
import os
import re
from fastapi import FastAPI, BackgroundTasks, Query
from pydantic import BaseModel
from dotenv import load_dotenv

from agent import run_summarize_agent

load_dotenv()

API_KEY = os.getenv("API_KEY")

app = FastAPI()


class SummarizeRequest(BaseModel):
    url: str


def is_valid_url(url: str) -> bool:
    """简单的 URL 格式验证"""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))


@app.post("/summarize")
async def summarize(
    request: SummarizeRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Query(..., description="API Key")
):
    # 验证 API Key
    if api_key != API_KEY:
        return {"success": False}

    # 验证 URL 格式
    if not is_valid_url(request.url):
        return {"success": False}

    # 添加后台任务
    background_tasks.add_task(run_summarize_agent, request.url)

    return {"success": True}
```

**Step 2: Commit**

```bash
git add main.py
git commit -m "feat: 实现 FastAPI 服务"
```

---

### Task 5: 验证服务

**Step 1: 创建 .env 文件**

复制 `.env.example` 为 `.env`，填入实际配置值。

**Step 2: 安装依赖**

```bash
pip install -r requirements.txt
```

**Step 3: 启动服务**

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Step 4: 测试请求**

```bash
curl -X POST "http://localhost:8000/summarize?api_key=your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

预期响应：`{"success": true}`

---

## 完成检查清单

- [ ] requirements.txt 已创建
- [ ] .env.example 和 .gitignore 已创建
- [ ] agent.py 已实现
- [ ] main.py 已实现
- [ ] 服务可正常启动
- [ ] API 可正常响应
