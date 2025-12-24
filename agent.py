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
