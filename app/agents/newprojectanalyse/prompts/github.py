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
   - 访问 https://api.github.com/repos/{{owner}}/{{repo}} 获取 star、fork 数量
   - 访问 https://api.github.com/repos/{{owner}}/{{repo}}/commits?per_page=1 获取最后 commit 时间

2. 深入分析仓库内容，提取以下信息

3. 返回以下 JSON 结构：

{{
  "title": "项目名称-中文标题-{current_date}",
  "url": "{url}",
  "stats": {{
    "stars": 1234,
    "forks": 567,
    "last_commit": "2024-01-01"
  }},
  "overview": "项目概述（100-200字），介绍项目是什么、解决什么问题、核心价值...",
  "core_features": [
    "功能1: 详细描述",
    "功能2: 详细描述",
    "功能3: 详细描述",
    "... 完整列出所有主要功能（5-15个）"
  ],
  "tech_stack": {{
    "languages": ["TypeScript", "Python"],
    "frameworks": ["React", "FastAPI", "Tailwind CSS"],
    "infrastructure": ["PostgreSQL", "Redis", "Docker"],
    "tools": ["esbuild", "Vite", "pnpm"]
  }},
  "architecture": [
    {{"module": "src/", "children": ["cli.ts - 命令行入口", "index.ts - 主模块", "utils/ - 工具函数"]}},
    {{"module": "ui/", "children": ["components/ - UI组件", "hooks/ - React Hooks"]}}
  ],
  "key_config": [
    {{"name": "配置项1", "description": "配置说明和用途"}},
    {{"name": "配置项2", "description": "配置说明和用途"}}
  ],
  "highlights": [
    "亮点1: 独特的设计或实现方式",
    "亮点2: 创新的解决方案",
    "亮点3: 性能优化或架构优势"
  ],
  "key_commands": [
    {{"command": "npm start", "description": "启动服务"}},
    {{"command": "npm run build", "description": "构建项目"}},
    {{"command": "npm test", "description": "运行测试"}}
  ],
  "deployment": {{
    "requirements": "环境要求，如 Node.js >= 18、Python 3.10+ 等",
    "install_steps": "安装步骤，如 npm install 或 pip install -r requirements.txt",
    "start_command": "启动命令，如 npm start 或 python main.py"
  }},
  "task_time": "{current_time}"
}}

## 字段说明

- **core_features**: 完整列出项目的所有核心功能（5-15个），每个功能用简洁的描述说明其作用
- **tech_stack**: 分类列出技术栈
  - languages: 编程语言
  - frameworks: 框架和主要依赖库
  - infrastructure: 数据库、缓存、消息队列等基础设施（如果有）
  - tools: 构建工具、开发工具
- **architecture**: 项目的目录结构和模块划分，帮助理解代码组织
- **key_config**: 项目的关键配置项，如环境变量、配置文件中的重要设置
- **highlights**: 项目的设计亮点、创新点或独特之处（3-7个）
- **key_commands**: 常用的命令，从 package.json scripts、Makefile、README 中提取

## 重要提示

- 使用 mcp__fetch__fetch 工具访问 GitHub API 获取统计信息
- title 格式必须为: "项目名称-中文标题-{current_date}"（中文标题10字以内）
- stats 中的数据必须从 GitHub API 实际获取
- core_features 要尽可能完整，不要遗漏重要功能
- tech_stack 中 infrastructure 和 tools 如果项目中没有可以为空数组
- key_config 从配置文件、README、环境变量说明中提取
- key_commands 从 package.json scripts、Makefile、README 命令说明中提取
- task_time 已预设为 {current_time}
"""
