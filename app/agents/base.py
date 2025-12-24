import time
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

            logger.finish(success=True, num_turns=num_turns, cost_usd=cost_usd)

        except Exception as e:
            logger.log_error(e)
            logger.finish(success=False, error=str(e), num_turns=num_turns, cost_usd=cost_usd)
