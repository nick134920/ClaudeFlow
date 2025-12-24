# Agent 详细日志记录设计方案

## 概述

增强 Agent 日志记录功能，详细记录 Agent 执行过程中的所有操作，便于调试定位问题。

## 需求

| 维度 | 选择 |
|------|------|
| 目的 | 调试定位问题 |
| 记录内容 | 思考过程 + 工具调用/返回 + 对话历史 |
| 格式 | 单文件按时间顺序 |
| 大内容处理 | 完整记录不截断 |
| 思考过程 | Thinking Block + TextBlock 都记录 |

## 日志文件结构

路径：`logs/{date}/tasks/{task_id}.log`

格式：
```
================================================================================
Task ID: summarize-001
Started: 2025-12-24 22:21:06
Input: {"url": "https://example.com"}
================================================================================

[22:21:06] [USER] Prompt
────────────────────────────────────────
（完整的 prompt 内容）
────────────────────────────────────────

[22:21:06] === TURN 1 ===

[22:21:08] [THINKING]
────────────────────────────────────────
（Claude 的思考过程）
────────────────────────────────────────

[22:21:08] [TEXT]
────────────────────────────────────────
（Claude 的文本回复）
────────────────────────────────────────

[22:21:08] [TOOL_CALL] tool_name (call_id)
────────────────────────────────────────
（工具调用参数 JSON）
────────────────────────────────────────

[22:21:12] [TOOL_RESULT] tool_name (call_id) ✓/✗ 耗时
────────────────────────────────────────
（完整的工具返回内容）
────────────────────────────────────────

================================================================================
Finished: 2025-12-24 22:21:21
Duration: 15.3s
Turns: 3
Cost: $0.0234
Status: SUCCESS/FAILED
Error: （如果失败，记录错误信息）
================================================================================
```

## 需要捕获的消息类型

| 消息类型 | 来源 | 记录内容 |
|----------|------|----------|
| 用户 Prompt | 初始调用 | 完整的 prompt 文本 |
| ThinkingBlock | AssistantMessage.content | Claude 的推理过程 |
| TextBlock | AssistantMessage.content | Claude 的文本回复 |
| ToolUseBlock | AssistantMessage.content | 工具名称 + 调用参数 + call_id |
| ToolResultBlock | UserMessage.content | 工具返回内容 + 是否出错 + 耗时 |
| ResultMessage | 流结束 | 总轮数、总耗时、API 成本 |
| 异常 | try/catch | 完整的错误堆栈 |

## 代码改动范围

### 1. app/core/logging.py - TaskLogger 类增强

```python
class TaskLogger:
    # 新增方法:

    def log_user_prompt(self, prompt: str) -> None:
        """记录用户 Prompt"""

    def log_thinking(self, content: str) -> None:
        """记录 Claude 思考过程"""

    def log_text(self, content: str) -> None:
        """记录 Claude 文本回复"""

    def log_tool_call(self, tool_name: str, call_id: str, params: dict) -> None:
        """记录工具调用（增加 call_id 参数）"""

    def log_tool_result(self, tool_name: str, call_id: str,
                        content: str, is_error: bool, duration: float) -> None:
        """记录工具返回（增加完整内容）"""

    def log_turn_start(self, turn_number: int) -> None:
        """记录轮次开始"""

    def log_error(self, error: Exception) -> None:
        """记录完整错误堆栈"""
```

### 2. app/agents/base.py - BaseAgent.run() 方法增强

- 增加 turn 计数器
- 记录初始 prompt
- 解析并记录 ThinkingBlock、TextBlock
- 记录完整的 ToolResultBlock 内容
- 捕获异常时记录完整堆栈

### 3. app/agents/summarize/config.py - 可选配置

```python
# 是否启用 extended thinking
ENABLE_THINKING = True
```
