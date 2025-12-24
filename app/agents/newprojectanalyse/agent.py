from claude_agent_sdk import ClaudeAgentOptions

from app.agents.base import BaseAgent
from app.agents.newprojectanalyse.config import NOTION_PARENT_PAGE_ID, MAX_TURNS, MCP_SERVERS


class NewProjectAnalyseAgent(BaseAgent):
    """新项目分析 Agent - 抓取项目 URL 内容并创建 Notion 页面"""

    MODULE_NAME = "newprojectanalyse"

    def get_prompt(self, url: str) -> str:
        return f"""
请完成以下任务：

1. 使用 mcp__firecrawl__firecrawl_scrape 工具抓取这个 URL 的内容：{url}

2. 为抓取的内容生成一个简洁的中文标题（10字以内）

3. 将内容总结为 Markdown 格式，包含：
   - 核心要点（3-5 条）
   - 详细总结（200-300字）

4. 使用 mcp__notion__API-post-page 工具在父页面 {NOTION_PARENT_PAGE_ID} 下创建一个新 Page：
   - 标题：生成的中文标题
   - 内容：Markdown 格式的总结
   - 内容顶部增加原始项目URL {url}
"""

    def get_options(self) -> ClaudeAgentOptions:
        return ClaudeAgentOptions(
            max_turns=MAX_TURNS,
            permission_mode="bypassPermissions",  # 自动批准所有工具使用
            mcp_servers=MCP_SERVERS,
        )

    def get_input_data(self, url: str) -> dict:
        return {"url": url}


async def run_newprojectanalyse_agent(url: str) -> None:
    """执行 newprojectanalyse Agent"""
    agent = NewProjectAnalyseAgent()
    await agent.run(url=url)
