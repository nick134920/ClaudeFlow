"""Notion API 服务封装"""
import json
import re
import time
import logging

from notion_client import Client
from notion_client.errors import APIResponseError

logger = logging.getLogger(__name__)


class NotionWriteError(Exception):
    """Notion 写入失败异常"""
    pass


class BlockBuilder:
    """Notion 块类型构建辅助类"""

    @staticmethod
    def _rich_text(content: str, link: str = None) -> list:
        """构建 rich_text 数组"""
        # Notion API 限制单个 rich_text 内容最大 2000 字符
        if len(content) > 2000:
            logger.warning(
                f"内容长度 {len(content)} 超过 Notion API 限制 2000 字符，将被截断"
            )
            content = content[:2000]
        text_obj = {"content": content}
        if link:
            text_obj["link"] = {"url": link}
        return [{"type": "text", "text": text_obj}]

    @staticmethod
    def bookmark(url: str) -> dict:
        """构建书签块"""
        return {
            "object": "block",
            "type": "bookmark",
            "bookmark": {"url": url}
        }

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
    def bulleted_list_item(text: str, children: list[dict] = None) -> dict:
        """构建单个无序列表项"""
        block = {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": BlockBuilder._rich_text(text)}
        }
        if children:
            block["bulleted_list_item"]["children"] = children
        return block

    @staticmethod
    def bulleted_list(items: list) -> list[dict]:
        """
        构建无序列表块列表，支持嵌套结构

        items 格式:
        - 简单字符串: "item text"
        - 带子项的字典: {"text": "parent", "children": ["child1", "child2"]}
        """
        result = []
        for item in items:
            if isinstance(item, str):
                result.append(BlockBuilder.bulleted_list_item(item))
            elif isinstance(item, dict):
                text = item.get("text", "")
                children_items = item.get("children", [])
                children_blocks = BlockBuilder.bulleted_list(children_items) if children_items else None
                result.append(BlockBuilder.bulleted_list_item(text, children_blocks))
        return result

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

    # Notion 支持的代码语言列表
    SUPPORTED_LANGUAGES = {
        "abap", "abc", "agda", "arduino", "ascii art", "assembly", "bash", "basic",
        "bnf", "c", "c#", "c++", "clojure", "coffeescript", "coq", "css", "dart",
        "dhall", "diff", "docker", "ebnf", "elixir", "elm", "erlang", "f#", "flow",
        "fortran", "gherkin", "glsl", "go", "graphql", "groovy", "haskell", "hcl",
        "html", "idris", "java", "javascript", "json", "julia", "kotlin", "latex",
        "less", "lisp", "livescript", "llvm ir", "lua", "makefile", "markdown",
        "markup", "matlab", "mathematica", "mermaid", "nix", "notion formula",
        "objective-c", "ocaml", "pascal", "perl", "php", "plain text", "powershell",
        "prolog", "protobuf", "purescript", "python", "r", "racket", "reason", "ruby",
        "rust", "sass", "scala", "scheme", "scss", "shell", "smalltalk", "solidity",
        "sql", "swift", "toml", "typescript", "vb.net", "verilog", "vhdl",
        "visual basic", "webassembly", "xml", "yaml", "java/c/c++/c#"
    }

    # 语言别名映射
    LANGUAGE_ALIASES = {
        "http": "plain text",
        "sh": "shell",
        "js": "javascript",
        "ts": "typescript",
        "py": "python",
        "rb": "ruby",
        "yml": "yaml",
        "dockerfile": "docker",
        "plaintext": "plain text",
        "text": "plain text",
        "txt": "plain text",
        "objective_c": "objective-c",
        "objc": "objective-c",
        "csharp": "c#",
        "cpp": "c++",
        "fsharp": "f#",
        "vbnet": "vb.net",
    }

    @staticmethod
    def _normalize_language(language: str) -> str:
        """将语言名称标准化为 Notion 支持的格式"""
        lang_lower = language.lower().strip()
        # 检查别名
        if lang_lower in BlockBuilder.LANGUAGE_ALIASES:
            return BlockBuilder.LANGUAGE_ALIASES[lang_lower]
        # 检查是否直接支持
        if lang_lower in BlockBuilder.SUPPORTED_LANGUAGES:
            return lang_lower
        # 回退到 plain text
        logger.warning(f"不支持的代码语言 '{language}'，回退到 'plain text'")
        return "plain text"

    @staticmethod
    def code(content: str, language: str = "plain text") -> dict:
        """构建代码块"""
        normalized_lang = BlockBuilder._normalize_language(language)
        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": BlockBuilder._rich_text(content),
                "language": normalized_lang
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

    @staticmethod
    def callout(text: str, emoji: str = "💡") -> dict:
        """构建标注块"""
        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": BlockBuilder._rich_text(text),
                "icon": {"type": "emoji", "emoji": emoji}
            }
        }


class NotionService:
    """Notion API 封装服务"""

    MAX_RETRIES = 3
    RETRY_DELAYS = [1, 2, 4]  # 指数退避（秒）
    MAX_BLOCKS_PER_REQUEST = 100  # Notion API 限制

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
        logger.info(f"创建 Notion 页面: {title}，共 {len(blocks)} 个块")

        # 分批处理：首批用于创建页面，剩余批次追加
        first_batch = blocks[:self.MAX_BLOCKS_PER_REQUEST]
        remaining_blocks = blocks[self.MAX_BLOCKS_PER_REQUEST:]

        def _create():
            return self.client.pages.create(
                parent={"page_id": parent_page_id},
                properties={
                    "title": [{"text": {"content": title}}]
                },
                children=first_batch
            )

        result = self._retry_operation(_create)
        page_id = result["id"]
        page_url = result.get("url", "")
        logger.info(f"页面创建成功: {page_id}, URL: {page_url}")

        # 追加剩余块
        if remaining_blocks:
            logger.info(f"需追加 {len(remaining_blocks)} 个块")
            for i in range(0, len(remaining_blocks), self.MAX_BLOCKS_PER_REQUEST):
                batch = remaining_blocks[i:i + self.MAX_BLOCKS_PER_REQUEST]
                self.append_blocks(page_id, batch)

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

        elif block_type == "bookmark":
            result.append(BlockBuilder.bookmark(block.get("url", "")))

        elif block_type == "to_do":
            result.append(BlockBuilder.to_do(
                block.get("content", ""),
                block.get("checked", False)
            ))

        elif block_type == "callout":
            result.append(BlockBuilder.callout(
                block.get("content", ""),
                block.get("emoji", "💡")
            ))

        else:
            logger.warning(f"未知的块类型: {block_type}，跳过")

    return result
