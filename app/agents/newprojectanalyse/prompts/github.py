# app/agents/newprojectanalyse/prompts/github.py
from datetime import datetime


def get_github_prompt(url: str, summary: str, content: str) -> str:
    """获取 GitHub 仓库分析的 Prompt"""
    current_date = datetime.now().strftime("%Y%m%d")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""
请分析以下 GitHub 仓库：{url}

## 仓库信息（由 gitingest 获取）

### 概要
{summary}

### 文件内容
{content}

## 任务

1. 从 URL 中提取 owner 和 repo，使用 GitHub API 获取项目统计信息：
   - 访问 https://api.github.com/repos/{{owner}}/{{repo}} 获取 star、fork 数量和最后更新时间
   - 访问 https://api.github.com/repos/{{owner}}/{{repo}}/commits?per_page=1 获取最后 commit 时间

2. 基于以上内容，生成项目总结

3. 识别项目名称，并生成一个简洁的中文标题（10字以内）

4. 返回以下 JSON 结构：

{{
  "title": "项目名称-中文标题-{current_date}",
  "url": "{url}",
  "stats": {{
    "stars": 1234,
    "forks": 567,
    "last_commit": "2024-01-01"
  }},
  "overview": "项目概述（100-200字），介绍项目是什么、解决什么问题...",
  "key_points": [
    "核心要点1",
    "核心要点2",
    "核心要点3",
    "核心要点4",
    "核心要点5"
  ],
  "detailed_summary": "200-300字的详细总结，包含技术栈、主要功能、设计亮点等...",
  "architecture": [
    {{"module": "主要模块1", "children": ["子模块1.1", "子模块1.2"]}},
    {{"module": "主要模块2", "children": ["子模块2.1", "子模块2.2"]}}
  ],
  "deployment": {{
    "requirements": "环境要求，如 Node.js >= 18、Python 3.10+ 等",
    "install_steps": "安装步骤，如 npm install 或 pip install -r requirements.txt",
    "start_command": "启动命令，如 npm start 或 python main.py"
  }},
  "task_time": "{current_time}"
}}

**重要:**
- 使用 mcp__fetch__fetch 工具访问 GitHub API 获取统计信息
- title 格式必须为: "项目名称-中文标题-{current_date}"
- stats 中的数据必须从 GitHub API 实际获取
- key_points 必须包含 3-7 个要点
- architecture 描述项目的核心模块结构
- deployment 从 README、Dockerfile、package.json 等文件中提取
- task_time 已预设为 {current_time}
"""
