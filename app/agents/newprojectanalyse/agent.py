from datetime import datetime

from claude_agent_sdk import ClaudeAgentOptions

from app.agents.base import BaseAgent
from app.agents.newprojectanalyse.config import MODEL, NOTION_PARENT_PAGE_ID, MAX_TURNS, MCP_SERVERS


class NewProjectAnalyseAgent(BaseAgent):
    """新项目分析 Agent - 抓取项目 URL 内容并创建 Notion 页面"""

    MODULE_NAME = "newprojectanalyse"

    def get_prompt(self, url: str) -> str:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""
请完成以下任务：

1. 使用 mcp__firecrawl__firecrawl_scrape 工具抓取这个 URL 的内容：{url}

2. 为抓取的内容生成一个简洁的中文标题（10字以内）

3. 将内容总结为结构化内容, 包含：
   - github项目则增加star数量, fork数量, 项目最后commit距离时间
   - 核心要点（3-5 条）
   - 详细总结（200-300字）
   - 以列表形式的多层级项目核心逻辑思维导图
- 确保结构化内容符合格式:
    - children参数以对象数组的形式处理
    - 内容中移除icon参数，只提供必要的参数
    

4. 使用 mcp__notion__API-post-page 工具在父页面 {NOTION_PARENT_PAGE_ID} 下创建一个新 Page：
   - 标题：生成的中文标题
   - 内容顶部增加任务时间 {current_time} 和notion超链接格式的原始项目URL {url}
   - 内容使用下方 Notion Block 规范构建

## Notion Page 规范

### 一、页面属性规范 (Page Properties)

页面属性定义在 `properties` 对象下。独立页面仅支持 `title` 属性。

**Title 属性（必需）**:
```json
"properties": {{
  "title": [{{ "text": {{ "content": "页面标题" }} }}]
}}
```

### 二、页面内容规范 (Page Content / Blocks)

页面正文由 `children` 数组构成，每个元素是一个块对象。

**常用块类型**:

1. **段落 (paragraph)**:
```json
{{ "type": "paragraph", "paragraph": {{ "rich_text": [{{ "type": "text", "text": {{ "content": "段落文字" }} }}] }} }}
```

2. **分级标题**: `heading_1`, `heading_2`, `heading_3`
```json
{{ "type": "heading_2", "heading_2": {{ "rich_text": [{{ "type": "text", "text": {{ "content": "标题文字" }} }}] }} }}
```

3. **无序列表 (bulleted_list_item)**:
```json
{{ "type": "bulleted_list_item", "bulleted_list_item": {{ "rich_text": [{{ "type": "text", "text": {{ "content": "列表项" }} }}] }} }}
```

4. **有序列表 (numbered_list_item)**:
```json
{{ "type": "numbered_list_item", "numbered_list_item": {{ "rich_text": [{{ "type": "text", "text": {{ "content": "列表项" }} }}] }} }}
```

5. **待办事项 (to_do)**:
```json
{{ "type": "to_do", "to_do": {{ "rich_text": [{{ "type": "text", "text": {{ "content": "任务" }} }}], "checked": false }} }}
```

6. **分割线 (divider)**:
```json
{{ "type": "divider", "divider": {{}} }}
```

7. **代码块 (code)**:
```json
{{ "type": "code", "code": {{ "rich_text": [{{ "type": "text", "text": {{ "content": "代码内容" }} }}], "language": "python" }} }}
```

**内容层级**: 块可以拥有 `children` 实现嵌套缩进。

### 三、创建页面完整示例

```json
{{
  "parent": {{ "page_id": "{NOTION_PARENT_PAGE_ID}" }},
  "icon": {{ "emoji": "📄" }},
  "properties": {{
    "title": [{{ "text": {{ "content": "页面标题" }} }}]
  }},
  "children": [
    {{ "type": "heading_1", "heading_1": {{ "rich_text": [{{ "type": "text", "text": {{ "content": "一级标题" }} }}] }} }},
    {{ "type": "paragraph", "paragraph": {{ "rich_text": [{{ "type": "text", "text": {{ "content": "正文内容" }} }}] }} }},
    {{ "type": "bulleted_list_item", "bulleted_list_item": {{ "rich_text": [{{ "type": "text", "text": {{ "content": "要点1" }} }}] }} }},
    {{ "type": "bulleted_list_item", "bulleted_list_item": {{ "rich_text": [{{ "type": "text", "text": {{ "content": "要点2" }} }}] }} }}
  ]
}}
```

"""

    def get_options(self) -> ClaudeAgentOptions:
        return ClaudeAgentOptions(
            model=MODEL,
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
