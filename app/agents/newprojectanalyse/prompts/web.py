# app/agents/newprojectanalyse/prompts/web.py
from datetime import datetime


def get_web_prompt(url: str) -> str:
    """获取网页分析的 Prompt"""
    current_date = datetime.now().strftime("%Y%m%d")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""
请完成以下任务：

1. 使用 mcp__firecrawl__firecrawl_scrape 工具抓取这个 URL 的内容：{url}

2. 识别网站/文章的名称，并生成一个简洁的中文标题（10字以内）

3. 分析网页内容，提取核心信息并总结

4. 将内容总结并输出为以下 JSON 格式（必须用 ```json 包裹）：

```json
{{
  "title": "网站名称-中文标题-{current_date}",
  "blocks": [
    {{"type": "bookmark", "url": "{url}"}},
    {{"type": "divider"}},
    {{"type": "heading_1", "content": "内容概述"}},
    {{"type": "paragraph", "content": "网页内容的简要概述..."}},
    {{"type": "heading_1", "content": "核心要点"}},
    {{"type": "bulleted_list", "items": ["要点1", "要点2", "要点3", "要点4", "要点5"]}},
    {{"type": "heading_1", "content": "详细总结"}},
    {{"type": "paragraph", "content": "200-300字的详细总结，包含主要观点、关键信息等..."}},
    {{"type": "heading_1", "content": "内容结构"}},
    {{"type": "bulleted_list", "items": [
      {{"text": "主要章节1", "children": ["子内容1.1", "子内容1.2"]}},
      {{"text": "主要章节2", "children": ["子内容2.1", "子内容2.2"]}}
    ]}},
    {{"type": "divider"}},
    {{"type": "paragraph", "content": "任务时间: {current_time}"}}
  ]
}}
```

**支持的块类型:**
- heading_1, heading_2, heading_3: 标题（content 字段）
- paragraph: 段落（content 字段）
- bulleted_list: 无序列表，支持两种格式:
  - 简单列表: items 为字符串数组 ["item1", "item2"]
  - 嵌套列表: items 为对象数组 [{{"text": "父项", "children": ["子项1", "子项2"]}}]
- numbered_list: 有序列表（items 字段，字符串数组）
- code: 代码块（content 和 language 字段）
- divider: 分割线（无额外字段）
- bookmark: 书签链接（url 字段）
- callout: 标注块（content 和 emoji 字段）
- to_do: 待办事项（content 和 checked 字段）

**重要:**
- title 格式必须为: "网站名称-中文标题-{current_date}"
- 任务时间必须放在内容最后
- 最终必须输出上述 JSON 格式
- JSON 必须用 ```json 代码块包裹
- 确保 JSON 格式正确，可以被解析
"""
