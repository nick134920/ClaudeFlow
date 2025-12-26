# app/agents/newprojectanalyse/agent.py
import re

from claude_agent_sdk import ClaudeAgentOptions

from app.agents.base import BaseAgent
from app.agents.newprojectanalyse.config import (
    MODEL,
    NOTION_TOKEN,
    NOTION_PARENT_PAGE_ID,
    MAX_TURNS,
    MCP_SERVERS,
    GITHUB_EXCLUDE_PATTERNS,
    GITHUB_INCLUDE_PATTERNS,
)
from app.agents.newprojectanalyse.handlers import (
    get_github_agent_definition,
    get_web_agent_definition,
)
from app.agents.newprojectanalyse.prompts import get_dispatcher_prompt
from app.services.notion import (
    NotionService,
    parse_agent_output,
    blocks_to_notion_format,
)


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
        include_patterns=GITHUB_INCLUDE_PATTERNS,
        exclude_patterns=GITHUB_EXCLUDE_PATTERNS,
    )
    return summary, tree, content


class NewProjectAnalyseAgent(BaseAgent):
    """新项目分析 Agent - 入口分发器"""

    MODULE_NAME = "newprojectanalyse"

    def __init__(self):
        super().__init__()
        self._url: str = ""
        self._github_content: tuple[str, str, str] | None = None

    async def pre_run(self, logger, **kwargs) -> dict:
        """
        运行前预处理：判断是否为 GitHub 仓库并获取内容

        Args:
            logger: TaskLogger 实例
            **kwargs: 包含 url 参数

        Returns:
            dict: 包含 github_content 的额外参数
        """
        url = kwargs.get("url")
        if not url:
            raise ValueError("url 参数是必需的")

        self._url = url
        self._github_content = None

        if is_github_repo_url(url):
            logger.info("检测到 GitHub 仓库 URL，使用 gitingest 获取内容...")
            try:
                self._github_content = await fetch_github_repo_content(url)
                logger.info("gitingest 获取成功")
            except Exception as e:
                logger.warning(f"gitingest 获取失败，回退到 web 分析: {e}")
                self._github_content = None

        return {"github_content": self._github_content}

    def get_prompt(self, url: str, github_content: tuple[str, str, str] | None = None, **kwargs) -> str:
        """生成入口 agent 的分发 prompt"""
        return get_dispatcher_prompt(url, github_content)

    def get_options(self) -> ClaudeAgentOptions:
        """注册所有 subagent"""
        agents = {}

        if self._github_content:
            summary, _tree, content = self._github_content
            agents["github_analyser"] = get_github_agent_definition(
                self._url, summary, content
            )
        else:
            agents["web_analyser"] = get_web_agent_definition(self._url)

        return ClaudeAgentOptions(
            model=MODEL,
            max_turns=MAX_TURNS,
            permission_mode="bypassPermissions",
            mcp_servers=MCP_SERVERS,
            agents=agents,
            allowed_tools=["Task"],
        )

    def get_input_data(self, url: str) -> dict:
        return {"url": url}

    async def process_final_output(self, final_text: str, **kwargs) -> None:
        """聚合 subagent 结果，写入 Notion"""
        if not final_text:
            return

        parsed = parse_agent_output(final_text)
        notion_blocks = blocks_to_notion_format(parsed["blocks"])

        notion_service = NotionService(NOTION_TOKEN)
        notion_service.create_page(
            parent_page_id=NOTION_PARENT_PAGE_ID,
            title=parsed["title"],
            blocks=notion_blocks,
        )


async def run_newprojectanalyse_agent(url: str) -> None:
    """执行 newprojectanalyse Agent"""
    agent = NewProjectAnalyseAgent()
    await agent.run(url=url)
