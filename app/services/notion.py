"""Notion API 服务封装"""
import time
import logging
import json
import re

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
        # Notion API 限制单个 rich_text 内容最大 2000 字符
        if len(content) > 2000:
            logger.warning(
                f"内容长度 {len(content)} 超过 Notion API 限制 2000 字符，将被截断"
            )
            content = content[:2000]
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
                logger.warning(
                    f"非 API 错误 (尝试 {attempt + 1}/{self.MAX_RETRIES}): {e}"
                )
                if attempt < self.MAX_RETRIES - 1:
                    # 非 API 错误使用较短的重试延迟
                    delay = 1
                    logger.info(f"等待 {delay} 秒后重试...")
                    time.sleep(delay)

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
