# 工程化重构实现计划

> 日期: 2024-12-24
> 目标: 将项目重构为工程化架构，增加日志模块

---

## 设计决策摘要

| 决策项 | 选择 |
|--------|------|
| 架构风格 | 领域驱动模块化（agent 在模块内，路由/模型在公共层） |
| 日志存储 | 文件系统，按日期目录 |
| 日志格式 | 请求日志 JSON，任务日志纯文本 |
| 任务 ID | 模块前缀+序号（summarize-001），按日期重置 |
| 日志捕获 | 实时流式写入 |
| 配置管理 | 分层（全局 + 模块级） |
| 错误处理 | 静默失败，只记录日志 |

---

## 目标目录结构

```
new-project-autoanalyse/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # 全局配置
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py           # 路由注册
│   │   └── models.py           # 请求/响应模型
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── logging.py          # 日志管理器
│   │   └── task_registry.py    # 任务 ID 生成
│   │
│   └── agents/
│       ├── __init__.py
│       ├── base.py             # Agent 基类
│       └── summarize/
│           ├── __init__.py
│           ├── config.py       # 模块配置
│           └── agent.py        # summarize agent
│
├── logs/                       # 日志目录（运行时创建）
├── run.py                      # 启动脚本
├── .env
├── .env.example
└── requirements.txt
```

---

## 实现任务

### 任务 1: 创建目录结构

**文件**: 创建以下空目录和 `__init__.py` 文件

```bash
mkdir -p app/api app/core app/agents/summarize
touch app/__init__.py
touch app/api/__init__.py
touch app/core/__init__.py
touch app/agents/__init__.py
touch app/agents/summarize/__init__.py
```

**验证**: 目录结构存在

---

### 任务 2: 实现全局配置 (app/config.py)

**文件**: `/Users/nick/Syncthing/Develop/AI/claude-code-agent-sdk/new-project-autoanalyse/app/config.py`

**依赖**: 无

**代码**:
```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 全局配置
API_KEY: str = os.getenv("API_KEY", "")
LOG_DIR: Path = BASE_DIR / os.getenv("LOG_DIR", "logs")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
```

**验证**: 导入 `from app.config import API_KEY, LOG_DIR` 成功

---

### 任务 3: 实现 summarize 模块配置 (app/agents/summarize/config.py)

**文件**: `/Users/nick/Syncthing/Develop/AI/claude-code-agent-sdk/new-project-autoanalyse/app/agents/summarize/config.py`

**依赖**: 无

**代码**:
```python
import os
from dotenv import load_dotenv

load_dotenv()

# summarize 模块配置（使用 SUMMARIZE_ 前缀）
NOTION_PARENT_PAGE_ID: str = os.getenv("SUMMARIZE_NOTION_PARENT_PAGE_ID", "")
MAX_TURNS: int = int(os.getenv("SUMMARIZE_MAX_TURNS", "15"))
```

**验证**: 导入 `from app.agents.summarize.config import NOTION_PARENT_PAGE_ID` 成功

---

### 任务 4: 实现任务 ID 注册器 (app/core/task_registry.py)

**文件**: `/Users/nick/Syncthing/Develop/AI/claude-code-agent-sdk/new-project-autoanalyse/app/core/task_registry.py`

**依赖**: 无

**功能**:
- 为每个模块维护独立的序号计数器
- 按日期重置序号
- 线程安全

**代码**:
```python
import threading
from datetime import date
from typing import Dict


class TaskRegistry:
    """任务 ID 注册器 - 生成 {module}-{sequence:03d} 格式的任务 ID"""

    def __init__(self):
        self._lock = threading.Lock()
        self._counters: Dict[str, int] = {}  # module -> counter
        self._current_date: date = date.today()

    def _reset_if_new_day(self) -> None:
        """如果日期变化，重置所有计数器"""
        today = date.today()
        if today != self._current_date:
            self._counters.clear()
            self._current_date = today

    def generate_id(self, module: str) -> str:
        """
        生成任务 ID

        Args:
            module: 模块名称（如 "summarize"）

        Returns:
            任务 ID（如 "summarize-001"）
        """
        with self._lock:
            self._reset_if_new_day()
            self._counters[module] = self._counters.get(module, 0) + 1
            return f"{module}-{self._counters[module]:03d}"


# 全局单例
task_registry = TaskRegistry()
```

**验证**:
```python
from app.core.task_registry import task_registry
assert task_registry.generate_id("summarize") == "summarize-001"
assert task_registry.generate_id("summarize") == "summarize-002"
assert task_registry.generate_id("translate") == "translate-001"
```

---

### 任务 5: 实现日志管理器 (app/core/logging.py)

**文件**: `/Users/nick/Syncthing/Develop/AI/claude-code-agent-sdk/new-project-autoanalyse/app/core/logging.py`

**依赖**: `app/config.py`

**功能**:
- `RequestLogger`: 记录 HTTP 请求日志（JSON 格式）
- `TaskLogger`: 记录任务执行日志（纯文本格式）
- 自动创建按日期组织的目录结构

**代码**:
```python
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict

from app.config import LOG_DIR, LOG_LEVEL


def _ensure_dir(path: Path) -> None:
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)


def _get_today_str() -> str:
    """获取今天的日期字符串 YYYY-MM-DD"""
    return datetime.now().strftime("%Y-%m-%d")


class RequestLogger:
    """
    请求日志记录器

    日志文件: logs/{date}/requests.log
    格式: JSON Lines
    """

    def __init__(self):
        self._logger = logging.getLogger("request")
        self._logger.setLevel(getattr(logging, LOG_LEVEL))
        self._current_date: Optional[str] = None
        self._handler: Optional[logging.FileHandler] = None

    def _ensure_handler(self) -> None:
        """确保日志处理器指向正确的日期文件"""
        today = _get_today_str()
        if self._current_date != today:
            # 移除旧处理器
            if self._handler:
                self._logger.removeHandler(self._handler)
                self._handler.close()

            # 创建新处理器
            log_dir = LOG_DIR / today
            _ensure_dir(log_dir)
            log_file = log_dir / "requests.log"

            self._handler = logging.FileHandler(log_file, encoding="utf-8")
            self._handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(self._handler)
            self._current_date = today

    def log(
        self,
        level: str,
        method: str,
        path: str,
        client_ip: str,
        task_id: Optional[str] = None,
        status: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        记录请求日志

        Args:
            level: 日志级别 (INFO, WARNING, ERROR)
            method: HTTP 方法
            path: 请求路径
            client_ip: 客户端 IP
            task_id: 任务 ID（可选）
            status: 状态（可选）
            extra: 额外字段（可选）
        """
        self._ensure_handler()

        record = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "method": method,
            "path": path,
            "client_ip": client_ip,
        }
        if task_id:
            record["task_id"] = task_id
        if status:
            record["status"] = status
        if extra:
            record.update(extra)

        log_method = getattr(self._logger, level.lower(), self._logger.info)
        log_method(json.dumps(record, ensure_ascii=False))


class TaskLogger:
    """
    任务日志记录器

    日志文件: logs/{date}/tasks/{task_id}.log
    格式: 纯文本
    """

    def __init__(self, task_id: str, input_data: Dict[str, Any]):
        self.task_id = task_id
        self.input_data = input_data
        self.start_time = datetime.now()

        # 创建日志文件
        today = _get_today_str()
        log_dir = LOG_DIR / today / "tasks"
        _ensure_dir(log_dir)
        self.log_file = log_dir / f"{task_id}.log"

        # 写入头部
        self._write_header()

    def _write_header(self) -> None:
        """写入日志文件头部"""
        header = f"""{'=' * 80}
Task ID: {self.task_id}
Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
Input: {json.dumps(self.input_data, ensure_ascii=False)}
{'=' * 80}

"""
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write(header)

    def _get_timestamp(self) -> str:
        """获取当前时间戳 [HH:MM:SS]"""
        return datetime.now().strftime("[%H:%M:%S]")

    def log(self, message: str) -> None:
        """记录一条日志"""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{self._get_timestamp()} {message}\n")

    def log_tool_call(self, tool_name: str, params: Dict[str, Any]) -> None:
        """记录工具调用"""
        params_str = json.dumps(params, ensure_ascii=False, indent=11)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{self._get_timestamp()} 工具调用: {tool_name}\n")
            f.write(f"           参数: {params_str}\n")

    def log_tool_result(self, success: bool, duration: float) -> None:
        """记录工具返回结果"""
        status = "成功" if success else "失败"
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{self._get_timestamp()} 工具返回: {status} ({duration:.1f}s)\n")

    def finish(self, success: bool, error: Optional[str] = None) -> None:
        """完成日志记录"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        status = "SUCCESS" if success else "FAILED"

        footer = f"""
{'=' * 80}
Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {duration:.1f}s
Status: {status}
"""
        if error:
            footer += f"Error: {error}\n"
        footer += "=" * 80 + "\n"

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(footer)


# 全局请求日志记录器
request_logger = RequestLogger()
```

**验证**:
```python
from app.core.logging import request_logger, TaskLogger

# 测试请求日志
request_logger.log("INFO", "POST", "/summarize", "127.0.0.1", task_id="summarize-001", status="accepted")

# 测试任务日志
task_logger = TaskLogger("summarize-001", {"url": "https://example.com"})
task_logger.log("Agent 启动")
task_logger.log_tool_call("firecrawl_scrape", {"url": "https://example.com"})
task_logger.log_tool_result(True, 2.1)
task_logger.finish(True)
```

检查生成的日志文件内容符合预期。

---

### 任务 6: 实现 Agent 基类 (app/agents/base.py)

**文件**: `/Users/nick/Syncthing/Develop/AI/claude-code-agent-sdk/new-project-autoanalyse/app/agents/base.py`

**依赖**: `app/core/logging.py`, `app/core/task_registry.py`

**功能**:
- 封装 Agent 执行的通用逻辑
- 自动生成任务 ID
- 实时流式记录 Agent 步骤
- 异常处理和日志记录

**代码**:
```python
import time
from abc import ABC, abstractmethod
from typing import Any, Dict

from claude_agent_sdk import query, ClaudeAgentOptions

from app.core.logging import TaskLogger
from app.core.task_registry import task_registry


class BaseAgent(ABC):
    """Agent 基类 - 封装通用的执行和日志逻辑"""

    # 子类必须定义模块名称
    MODULE_NAME: str = ""

    def __init__(self):
        if not self.MODULE_NAME:
            raise ValueError("子类必须定义 MODULE_NAME")

    @abstractmethod
    def get_prompt(self, **kwargs) -> str:
        """获取 Agent 提示词"""
        pass

    @abstractmethod
    def get_options(self) -> ClaudeAgentOptions:
        """获取 Agent 配置选项"""
        pass

    def get_input_data(self, **kwargs) -> Dict[str, Any]:
        """获取用于日志记录的输入数据"""
        return kwargs

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

        logger.log("Agent 启动")

        prompt = self.get_prompt(**kwargs)
        options = self.get_options()

        tool_start_time: float = 0

        try:
            async for message in query(prompt=prompt, options=options):
                # 记录工具调用
                if message.type == "tool_use":
                    tool_start_time = time.time()
                    tool_name = getattr(message, "name", "unknown")
                    tool_input = getattr(message, "input", {})
                    logger.log_tool_call(tool_name, tool_input)

                # 记录工具结果
                elif message.type == "tool_result":
                    duration = time.time() - tool_start_time if tool_start_time else 0
                    is_error = getattr(message, "is_error", False)
                    logger.log_tool_result(not is_error, duration)

            logger.log("Agent 完成")
            logger.finish(success=True)

        except Exception as e:
            error_msg = str(e)
            logger.log(f"Agent 异常: {error_msg}")
            logger.finish(success=False, error=error_msg)
```

**验证**: 能够被子类继承并正确执行

---

### 任务 7: 实现 summarize Agent (app/agents/summarize/agent.py)

**文件**: `/Users/nick/Syncthing/Develop/AI/claude-code-agent-sdk/new-project-autoanalyse/app/agents/summarize/agent.py`

**依赖**: `app/agents/base.py`, `app/agents/summarize/config.py`

**代码**:
```python
from claude_agent_sdk import ClaudeAgentOptions

from app.agents.base import BaseAgent
from app.agents.summarize.config import NOTION_PARENT_PAGE_ID, MAX_TURNS


class SummarizeAgent(BaseAgent):
    """URL 摘要 Agent - 抓取 URL 内容并创建 Notion 页面"""

    MODULE_NAME = "summarize"

    def get_prompt(self, url: str) -> str:
        return f"""
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

    def get_options(self) -> ClaudeAgentOptions:
        return ClaudeAgentOptions(
            max_turns=MAX_TURNS,
        )

    def get_input_data(self, url: str) -> dict:
        return {"url": url}


# 便捷函数（保持向后兼容）
async def run_summarize_agent(url: str) -> None:
    """执行 summarize Agent"""
    agent = SummarizeAgent()
    await agent.run(url=url)
```

**验证**: 能够正确执行并生成日志

---

### 任务 8: 实现请求/响应模型 (app/api/models.py)

**文件**: `/Users/nick/Syncthing/Develop/AI/claude-code-agent-sdk/new-project-autoanalyse/app/api/models.py`

**依赖**: 无

**代码**:
```python
import re
from pydantic import BaseModel, field_validator


class SummarizeRequest(BaseModel):
    """摘要请求模型"""
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(pattern, v):
            raise ValueError("无效的 URL 格式")
        return v


class TaskResponse(BaseModel):
    """通用任务响应模型"""
    success: bool
    task_id: str | None = None
    message: str | None = None
```

**验证**: 模型验证正常工作

---

### 任务 9: 实现路由 (app/api/routes.py)

**文件**: `/Users/nick/Syncthing/Develop/AI/claude-code-agent-sdk/new-project-autoanalyse/app/api/routes.py`

**依赖**: `app/api/models.py`, `app/agents/summarize/agent.py`, `app/config.py`, `app/core/logging.py`, `app/core/task_registry.py`

**代码**:
```python
from fastapi import APIRouter, BackgroundTasks, Query, Request
from pydantic import ValidationError

from app.api.models import SummarizeRequest, TaskResponse
from app.agents.summarize.agent import run_summarize_agent
from app.config import API_KEY
from app.core.logging import request_logger
from app.core.task_registry import task_registry

router = APIRouter()


def get_client_ip(request: Request) -> str:
    """获取客户端 IP"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/summarize", response_model=TaskResponse)
async def summarize(
    request: Request,
    body: SummarizeRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Query(..., description="API Key"),
):
    """
    提交 URL 摘要任务

    - 验证 API Key
    - 验证 URL 格式
    - 提交后台任务
    - 返回任务 ID
    """
    client_ip = get_client_ip(request)
    path = "/summarize"

    # 验证 API Key
    if api_key != API_KEY:
        request_logger.log(
            "WARNING", "POST", path, client_ip,
            status="rejected", extra={"reason": "invalid_api_key"}
        )
        return TaskResponse(success=False, message="Invalid API Key")

    # 生成任务 ID
    task_id = task_registry.generate_id("summarize")

    # 记录请求日志
    request_logger.log(
        "INFO", "POST", path, client_ip,
        task_id=task_id, status="accepted"
    )

    # 添加后台任务
    background_tasks.add_task(run_summarize_agent, body.url)

    return TaskResponse(success=True, task_id=task_id)
```

**验证**: API 端点正常响应

---

### 任务 10: 实现 FastAPI 主应用 (app/main.py)

**文件**: `/Users/nick/Syncthing/Develop/AI/claude-code-agent-sdk/new-project-autoanalyse/app/main.py`

**依赖**: `app/api/routes.py`

**代码**:
```python
from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="Agent API",
    description="工程化的 Agent 服务接口",
    version="1.0.0",
)

# 注册路由
app.include_router(router)
```

**验证**: FastAPI 应用能够启动

---

### 任务 11: 实现启动脚本 (run.py)

**文件**: `/Users/nick/Syncthing/Develop/AI/claude-code-agent-sdk/new-project-autoanalyse/run.py`

**依赖**: `app/main.py`

**代码**:
```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
```

**验证**: `python run.py` 能够启动服务

---

### 任务 12: 更新环境变量模板 (.env.example)

**文件**: `/Users/nick/Syncthing/Develop/AI/claude-code-agent-sdk/new-project-autoanalyse/.env.example`

**依赖**: 无

**内容**:
```env
# ============================================
# 全局配置
# ============================================
API_KEY=your-secret-key
LOG_DIR=logs
LOG_LEVEL=INFO

# ============================================
# summarize 模块配置
# ============================================
SUMMARIZE_NOTION_PARENT_PAGE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
SUMMARIZE_MAX_TURNS=15
```

**验证**: 文件内容正确

---

### 任务 13: 更新 .env 文件

**文件**: `/Users/nick/Syncthing/Develop/AI/claude-code-agent-sdk/new-project-autoanalyse/.env`

**操作**: 将现有的 `NOTION_PARENT_PAGE_ID` 重命名为 `SUMMARIZE_NOTION_PARENT_PAGE_ID`，添加新的配置项

**验证**: 配置能够正确加载

---

### 任务 14: 删除旧文件

**操作**: 删除项目根目录下的旧文件

```bash
rm main.py agent.py
```

**验证**: 旧文件已删除，新结构正常工作

---

### 任务 15: 更新 .gitignore

**文件**: `/Users/nick/Syncthing/Develop/AI/claude-code-agent-sdk/new-project-autoanalyse/.gitignore`

**添加内容**:
```
# 日志目录
logs/
```

**验证**: git status 不再显示 logs 目录

---

## 执行顺序

按以下顺序执行任务以确保依赖关系正确：

1. **任务 1**: 创建目录结构
2. **任务 2**: 全局配置
3. **任务 3**: summarize 模块配置
4. **任务 4**: 任务 ID 注册器
5. **任务 5**: 日志管理器
6. **任务 6**: Agent 基类
7. **任务 7**: summarize Agent
8. **任务 8**: 请求/响应模型
9. **任务 9**: 路由
10. **任务 10**: FastAPI 主应用
11. **任务 11**: 启动脚本
12. **任务 12-13**: 更新配置文件
14. **任务 14**: 删除旧文件
15. **任务 15**: 更新 .gitignore

---

## 验证清单

完成所有任务后，执行以下验证：

- [ ] `python run.py` 能够启动服务
- [ ] `curl -X POST "http://localhost:8000/summarize?api_key=xxx" -H "Content-Type: application/json" -d '{"url": "https://example.com"}'` 返回 `{"success": true, "task_id": "summarize-001"}`
- [ ] `logs/` 目录下生成按日期组织的日志文件
- [ ] `logs/2024-12-24/requests.log` 包含 JSON 格式的请求日志
- [ ] `logs/2024-12-24/tasks/summarize-001.log` 包含纯文本格式的任务执行日志，记录了 Agent 的每个步骤

---

## 扩展指南

### 添加新的 Agent 模块

以 `translate` 模块为例：

1. 创建目录: `mkdir app/agents/translate`
2. 创建 `__init__.py`
3. 创建 `config.py`:
   ```python
   import os
   from dotenv import load_dotenv
   load_dotenv()

   TARGET_LANGUAGE: str = os.getenv("TRANSLATE_TARGET_LANGUAGE", "zh")
   MAX_TURNS: int = int(os.getenv("TRANSLATE_MAX_TURNS", "10"))
   ```
4. 创建 `agent.py`:
   ```python
   from app.agents.base import BaseAgent
   from claude_agent_sdk import ClaudeAgentOptions
   from app.agents.translate.config import TARGET_LANGUAGE, MAX_TURNS

   class TranslateAgent(BaseAgent):
       MODULE_NAME = "translate"

       def get_prompt(self, text: str) -> str:
           return f"将以下内容翻译为{TARGET_LANGUAGE}:\n\n{text}"

       def get_options(self) -> ClaudeAgentOptions:
           return ClaudeAgentOptions(max_turns=MAX_TURNS)

   async def run_translate_agent(text: str) -> None:
       agent = TranslateAgent()
       await agent.run(text=text)
   ```
5. 在 `app/api/routes.py` 添加路由
6. 在 `.env` 添加 `TRANSLATE_*` 配置

---

## 变更摘要

| 现有文件 | 操作 |
|---------|------|
| `main.py` | 删除，功能拆分到 `app/` |
| `agent.py` | 删除，功能移动到 `app/agents/summarize/agent.py` |
| `.env.example` | 更新，添加新配置项 |
| `.env` | 更新，重命名配置项 |
| `.gitignore` | 更新，添加 logs/ |

| 新增文件 | 说明 |
|---------|------|
| `app/config.py` | 全局配置 |
| `app/main.py` | FastAPI 入口 |
| `app/api/models.py` | 请求/响应模型 |
| `app/api/routes.py` | API 路由 |
| `app/core/logging.py` | 日志管理器 |
| `app/core/task_registry.py` | 任务 ID 生成器 |
| `app/agents/base.py` | Agent 基类 |
| `app/agents/summarize/config.py` | summarize 模块配置 |
| `app/agents/summarize/agent.py` | summarize Agent |
| `run.py` | 启动脚本 |
