# Agent 详细日志记录实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 增强 Agent 日志记录功能，详细记录 Claude 思考过程、工具调用/返回、对话历史，便于调试定位问题。

**Architecture:** 扩展 TaskLogger 类添加新的日志方法，修改 BaseAgent.run() 解析所有消息类型并调用相应日志方法。

**Tech Stack:** Python 3.11, claude-agent-sdk

---

## Task 1: 扩展 TaskLogger 日志方法

**Files:**
- Modify: `app/core/logging.py:95-169`

**Step 1: 添加分隔线常量和新的日志方法**

在 `TaskLogger` 类中添加以下方法：

```python
class TaskLogger:
    """
    任务日志记录器

    日志文件: logs/{date}/tasks/{task_id}.log
    格式: 纯文本
    """

    SEPARATOR = "─" * 40

    def __init__(self, task_id: str, input_data: Dict[str, Any]):
        self.task_id = task_id
        self.input_data = input_data
        self.start_time = datetime.now()
        self.turn_count = 0
        self.tool_call_names: Dict[str, str] = {}  # call_id -> tool_name

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

    def log_user_prompt(self, prompt: str) -> None:
        """记录用户 Prompt"""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{self._get_timestamp()} [USER] Prompt\n")
            f.write(f"{self.SEPARATOR}\n")
            f.write(f"{prompt}\n")
            f.write(f"{self.SEPARATOR}\n\n")

    def log_turn_start(self) -> None:
        """记录轮次开始"""
        self.turn_count += 1
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{self._get_timestamp()} === TURN {self.turn_count} ===\n\n")

    def log_thinking(self, content: str) -> None:
        """记录 Claude 思考过程"""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{self._get_timestamp()} [THINKING]\n")
            f.write(f"{self.SEPARATOR}\n")
            f.write(f"{content}\n")
            f.write(f"{self.SEPARATOR}\n\n")

    def log_text(self, content: str) -> None:
        """记录 Claude 文本回复"""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{self._get_timestamp()} [TEXT]\n")
            f.write(f"{self.SEPARATOR}\n")
            f.write(f"{content}\n")
            f.write(f"{self.SEPARATOR}\n\n")

    def log_tool_call(self, tool_name: str, call_id: str, params: Dict[str, Any]) -> None:
        """记录工具调用"""
        self.tool_call_names[call_id] = tool_name
        params_str = json.dumps(params, ensure_ascii=False, indent=2)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{self._get_timestamp()} [TOOL_CALL] {tool_name} ({call_id})\n")
            f.write(f"{self.SEPARATOR}\n")
            f.write(f"{params_str}\n")
            f.write(f"{self.SEPARATOR}\n\n")

    def log_tool_result(
        self, call_id: str, content: Any, is_error: bool, duration: float
    ) -> None:
        """记录工具返回结果"""
        tool_name = self.tool_call_names.get(call_id, "unknown")
        status = "✗" if is_error else "✓"

        # 处理 content，可能是字符串或其他类型
        if isinstance(content, str):
            content_str = content
        else:
            content_str = json.dumps(content, ensure_ascii=False, indent=2)

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{self._get_timestamp()} [TOOL_RESULT] {tool_name} ({call_id}) {status} {duration:.1f}s\n")
            f.write(f"{self.SEPARATOR}\n")
            f.write(f"{content_str}\n")
            f.write(f"{self.SEPARATOR}\n\n")

    def log_error(self, error: Exception) -> None:
        """记录完整错误堆栈"""
        import traceback
        error_trace = traceback.format_exc()
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{self._get_timestamp()} [ERROR]\n")
            f.write(f"{self.SEPARATOR}\n")
            f.write(f"{error_trace}\n")
            f.write(f"{self.SEPARATOR}\n\n")

    def finish(self, success: bool, error: Optional[str] = None,
               num_turns: int = 0, cost_usd: float = 0) -> None:
        """完成日志记录"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        status = "SUCCESS" if success else "FAILED"

        footer = f"""
{'=' * 80}
Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {duration:.1f}s
Turns: {num_turns}
Cost: ${cost_usd:.4f}
Status: {status}
"""
        if error:
            footer += f"Error: {error}\n"
        footer += "=" * 80 + "\n"

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(footer)
```

**Step 2: 验证修改**

Run: `python -c "from app.core.logging import TaskLogger; print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add app/core/logging.py
git commit -m "feat(logging): 扩展 TaskLogger 支持详细日志记录"
```

---

## Task 2: 更新 BaseAgent 解析和记录所有消息类型

**Files:**
- Modify: `app/agents/base.py`

**Step 1: 更新导入语句**

```python
import time
import traceback
from abc import ABC, abstractmethod
from typing import Any, Dict

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    ToolUseBlock,
    ToolResultBlock,
    UserMessage,
    TextBlock,
    ThinkingBlock,
)

from app.core.logging import TaskLogger
from app.core.task_registry import task_registry
```

**Step 2: 重写 run() 方法**

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

    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                # 新的 Turn 开始
                logger.log_turn_start()

                # 解析 AssistantMessage 中的 content blocks
                msg_content = getattr(message, "message", None)
                if msg_content:
                    blocks = getattr(msg_content, "content", [])
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
                msg_content = getattr(message, "message", None)
                if msg_content:
                    blocks = getattr(msg_content, "content", [])
                    for block in blocks:
                        if isinstance(block, ToolResultBlock):
                            tool_id = getattr(block, "tool_use_id", "")
                            start_time = tool_start_times.get(tool_id, 0)
                            duration = time.time() - start_time if start_time else 0
                            is_error = getattr(block, "is_error", False)
                            content = getattr(block, "content", "")
                            logger.log_tool_result(tool_id, content, is_error, duration)

            elif isinstance(message, ResultMessage):
                cost_usd = getattr(message, "cost_usd", 0)
                num_turns = getattr(message, "num_turns", 0)

        logger.finish(success=True, num_turns=num_turns, cost_usd=cost_usd)

    except Exception as e:
        logger.log_error(e)
        logger.finish(success=False, error=str(e), num_turns=num_turns, cost_usd=cost_usd)
```

**Step 3: 验证导入**

Run: `python -c "from app.agents.base import BaseAgent; print('OK')"`
Expected: OK

**Step 4: Commit**

```bash
git add app/agents/base.py
git commit -m "feat(agent): 增强 Agent 日志记录所有消息类型"
```

---

## Task 3: 集成测试

**Files:**
- 无需修改文件

**Step 1: 启动服务测试**

Run: `cd /Users/nick/Syncthing/Develop/AI/claude-code-agent-sdk/new-project-autoanalyse && timeout 5 .venv/bin/python run.py || true`

Expected: 服务启动无报错（5秒后自动超时退出）

**Step 2: 检查日志格式**

手动发送一个测试请求后，检查日志文件格式是否正确：

```bash
# 找到最新的日志文件
ls -la logs/$(date +%Y-%m-%d)/tasks/
```

**Step 3: 最终提交**

```bash
git add -A
git commit -m "feat: Agent 详细日志记录功能完成"
```

---

## 完成标准

- [ ] TaskLogger 新增 6 个日志方法
- [ ] BaseAgent.run() 解析 ThinkingBlock、TextBlock、ToolUseBlock、ToolResultBlock
- [ ] 日志包含完整的工具调用参数和返回值
- [ ] 日志包含 Turn 计数
- [ ] 日志尾部包含 Turns 和 Cost 统计
- [ ] 服务正常启动无报错
