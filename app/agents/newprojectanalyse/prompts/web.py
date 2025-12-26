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

4. 返回以下 JSON 结构：

{{
  "title": "网站名称-中文标题-{current_date}",
  "url": "{url}",
  "overview": "内容概述（100-200字），介绍网页的主要内容...",
  "key_points": [
    "核心要点1",
    "核心要点2",
    "核心要点3",
    "核心要点4",
    "核心要点5"
  ],
  "detailed_summary": "200-300字的详细总结，包含主要观点、关键信息等...",
  "content_structure": [
    {{"section": "主要章节1", "children": ["子内容1.1", "子内容1.2"]}},
    {{"section": "主要章节2", "children": ["子内容2.1", "子内容2.2"]}}
  ],
  "task_time": "{current_time}"
}}

**重要:**
- title 格式必须为: "网站名称-中文标题-{current_date}"
- key_points 必须包含 3-7 个要点
- content_structure 描述网页的内容结构层次
- task_time 已预设为 {current_time}
"""
