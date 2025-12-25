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

    async def process_final_output(self, final_text: str, **kwargs) -> None:
        """
        处理 Agent 的最终文本输出（子类可覆盖）

        Args:
            final_text: Agent 输出的文本
            **kwargs: 传递给 run() 的参数
        """
        pass

    async def process_structured_output(self, structured_output: Any, **kwargs) -> None:
        """
        处理 Agent 的结构化输出（子类可覆盖）

        当使用 output_format 时，SDK 会返回 structured_output。
        此方法优先于 process_final_output 被调用。

        Args:
            structured_output: SDK 返回的结构化数据
            **kwargs: 传递给 run() 的参数
        """
        pass

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
        structured_output = None  # 结构化输出（使用 output_format 时）
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
                    structured_output = getattr(message, "structured_output", None)

            # 处理最终输出（优先使用结构化输出）
            logger.debug(f"[OUTPUT_DEBUG] structured_output is None: {structured_output is None}")
            logger.debug(f"[OUTPUT_DEBUG] structured_output type: {type(structured_output)}")
            logger.debug(f"[OUTPUT_DEBUG] structured_output value: {structured_output}")

            if structured_output is not None:
                logger.debug("[OUTPUT_DEBUG] 使用 structured_output 路径")
                await self.process_structured_output(structured_output, **kwargs)
            else:
                logger.debug("[OUTPUT_DEBUG] structured_output 为 None，进入回退逻辑")
                # 回退：收集最终文本输出（查找包含 JSON 的输出）
                final_text = ""
                checked_texts = []  # 记录检查过的文本
                for msg in reversed(messages_collected):
                    if isinstance(msg, AssistantMessage):
                        for block in getattr(msg, "content", []):
                            if isinstance(block, TextBlock):
                                text = getattr(block, "text", "")
                                if text:
                                    # 记录检查的文本片段
                                    text_preview = text[:200] + "..." if len(text) > 200 else text
                                    has_json_marker = "```json" in text
                                    has_raw_json = text.strip().startswith("{")
                                    checked_texts.append({
                                        "preview": text_preview,
                                        "has_json_marker": has_json_marker,
                                        "has_raw_json": has_raw_json,
                                        "length": len(text)
                                    })

                                    if has_json_marker:
                                        final_text = text
                                        logger.debug(f"[OUTPUT_DEBUG] 找到包含 ```json 的文本，长度: {len(text)}")
                                        break
                        if final_text:
                            break

                # 打印所有检查过的文本摘要
                logger.debug(f"[OUTPUT_DEBUG] 共检查 {len(checked_texts)} 个 TextBlock")
                for i, info in enumerate(checked_texts):
                    logger.debug(f"[OUTPUT_DEBUG] TextBlock[{i}]: length={info['length']}, "
                                 f"has_json_marker={info['has_json_marker']}, "
                                 f"has_raw_json={info['has_raw_json']}")
                    logger.debug(f"[OUTPUT_DEBUG] TextBlock[{i}] preview: {info['preview']}")

                if final_text:
                    logger.debug("[OUTPUT_DEBUG] 找到 final_text，调用 process_final_output")
                    await self.process_final_output(final_text, **kwargs)
                else:
                    logger.warning("[OUTPUT_DEBUG] 未找到符合条件的 final_text，跳过 process_final_output")

            logger.finish(success=True, num_turns=num_turns, cost_usd=cost_usd)

        except Exception as e:
            logger.log_error(e)
            logger.finish(success=False, error=str(e), num_turns=num_turns, cost_usd=cost_usd)
