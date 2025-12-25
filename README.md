# Claude Agent SDK 应用集合

基于 Claude Agent SDK 构建的多 Agent 应用系统，包含项目分析和深度研究两个核心功能。

## 项目说明

### 功能模块

#### 1. NewProjectAnalyse - 新项目分析

自动抓取 URL 内容、进行 AI 智能分析，并将结果存储到 Notion。

- **URL 智能抓取**：支持任意 URL，特别优化了 GitHub 项目的元数据提取（Stars、Fork、最后提交时间等）
- **AI 深度分析**：使用 Claude AI 模型对内容进行智能分析，生成结构化的中文摘要
- **Notion 自动归档**：分析结果自动创建为 Notion 页面，支持多层级思维导图格式

#### 2. DeepResearch - 深度研究

多 Agent 协作的深度研究系统，使用 Tavily 进行网络搜索，综合研究结果保存到 Notion。

- **多 Agent 协作**：Lead Agent 协调任务分解，Researcher 并行搜索，NotionWriter 综合报告
- **Tavily 搜索**：支持配置搜索深度、结果数量等参数
- **结构化输出**：自动在 Notion 父页面下创建子页面，包含执行摘要、研究详情、参考来源

### 通用特性

- **异步任务处理**：基于 FastAPI BackgroundTasks 实现请求即返回，后台异步执行
- **完整日志追踪**：详细记录每个任务的执行过程、工具调用、耗时和成本

### 技术架构

**NewProjectAnalyse 流程：**
```
客户端 HTTP 请求
    ↓
FastAPI 路由 (/newprojectanalyse)
    ↓
API 验证 + 任务 ID 生成
    ↓
后台队列 (BackgroundTasks)
    ↓
NewProjectAnalyseAgent.run()
    ├── Firecrawl MCP → 网页内容抓取
    ├── Notion MCP → 页面创建
    └── Claude Agent SDK → 多轮 AI 分析
    ↓
日志保存 + Notion 页面创建完成
```

**DeepResearch 流程：**
```
客户端 HTTP 请求
    ↓
FastAPI 路由 (/deepresearch)
    ↓
API 验证 + 任务 ID 生成
    ↓
后台队列 (BackgroundTasks)
    ↓
DeepResearchAgent.run()
    ↓
Lead Agent (协调者)
    ├── 分解主题为 2-4 个子课题
    └── 并行派发 Researcher subagent
          ↓
    ┌─────────┬─────────┐
    ↓         ↓         ↓
Researcher Researcher Researcher
(Tavily)   (Tavily)   (Tavily)
    ↓         ↓         ↓
    └─────────┴─────────┘
          ↓
    NotionWriter
    ├── 读取所有研究笔记
    └── 创建 Notion 子页面
          ↓
日志保存 + Notion 页面创建完成
```

### 技术栈

| 类型 | 技术 |
|------|------|
| 语言 | Python 3.11+ |
| Web 框架 | FastAPI + Uvicorn |
| AI 引擎 | Claude Agent SDK |
| MCP 服务 | Firecrawl（网页抓取）、Tavily（网络搜索）、Notion（页面管理） |
| 配置管理 | YAML |

## 部署说明

### 环境要求

- Python 3.11 或更高版本
- Node.js（用于运行 MCP 服务器）
- Firecrawl API Key（从 [firecrawl.dev](https://firecrawl.dev) 获取）
- Tavily API Key（从 [tavily.com](https://tavily.com) 获取，用于 DeepResearch）
- Notion Integration Token（从 [Notion Developers](https://www.notion.so/my-integrations) 获取）

### 安装步骤

1. **克隆项目**

```bash
git clone <repository-url>
cd new-project-autoanalyse
```

2. **安装 Python 依赖**

```bash
pip install -r requirements.txt
```

3. **配置文件**

复制示例配置并填入实际密钥：

```bash
cp config.yaml.example config.yaml
```

编辑 `config.yaml`：

```yaml
api_key: your-api-key-here  # 自定义 API 访问密钥

# NewProjectAnalyse 配置
newprojectanalyse:
  model: claude-haiku-4-5-20251001
  notion_parent_page_id: your-notion-page-id  # Notion 父页面 ID
  max_turns: 15
  mcp_servers:
    firecrawl:
      type: stdio
      command: npx
      args: ["-y", "firecrawl-mcp"]
      env:
        FIRECRAWL_API_KEY: your-firecrawl-key
    notion:
      type: stdio
      command: npx
      args: ["-y", "@notionhq/notion-mcp-server"]
      env:
        NOTION_TOKEN: your-notion-token

# DeepResearch 配置
deepresearch:
  model: claude-sonnet-4-20250514
  notion_parent_page_id: your-notion-page-id  # Notion 父页面 ID
  max_turns: 20
  tavily:
    search_depth: advanced  # basic | advanced
    max_results: 10
    include_images: false
  mcp_servers:
    tavily:
      type: stdio
      command: npx
      args: ["-y", "tavily-mcp@latest"]
      env:
        TAVILY_API_KEY: your-tavily-key
    notion:
      type: stdio
      command: npx
      args: ["-y", "@notionhq/notion-mcp-server"]
      env:
        NOTION_TOKEN: your-notion-token
```

4. **启动服务**

```bash
python run.py
```

服务将在 `http://0.0.0.0:8000` 启动。

### API 使用

#### NewProjectAnalyse - 新项目分析

```bash
curl -X POST "http://localhost:8000/newprojectanalyse?api_key=your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://github.com/example/project"}'
```

**响应示例**

```json
{
  "success": true,
  "task_id": "newprojectanalyse_251224_14_30_00"
}
```

#### DeepResearch - 深度研究

```bash
curl -X POST "http://localhost:8000/deepresearch?api_key=your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"topic":"2024年大语言模型发展趋势"}'
```

**响应示例**

```json
{
  "success": true,
  "task_id": "deepresearch_251225_11_30_00"
}
```

#### Agent 健康检查

```bash
curl "http://localhost:8000/check-agent-health?api_key=your-api-key"
```

**响应示例**

```json
// 成功
{
  "healthy": true,
  "response": "I am Claude, an AI assistant made by Anthropic...",
  "error": null
}

// 失败
{
  "healthy": false,
  "response": null,
  "error": "错误信息"
}
```

### 日志查看

任务执行日志保存在 `logs/` 目录：

```
logs/
└── 2025-12-24/
    ├── requests.log              # HTTP 请求日志（JSON Lines 格式）
    └── tasks/
        └── {task_id}.log         # 任务执行详情
```

### 生产环境部署

**方式一：直接运行**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**方式二：Docker Compose**

```bash
# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 ANTHROPIC_BASE_URL 和 ANTHROPIC_AUTH_TOKEN

# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 项目结构

```
claude-agent-sdk/
├── run.py                 # 应用入口
├── config.yaml            # 配置文件
├── config.yaml.example    # 配置示例
├── requirements.txt       # Python 依赖
├── app/
│   ├── main.py            # FastAPI 应用
│   ├── config.py          # 配置加载器
│   ├── api/
│   │   ├── routes.py      # API 路由
│   │   └── models.py      # 数据模型
│   ├── agents/
│   │   ├── base.py        # Agent 基类
│   │   ├── newprojectanalyse/
│   │   │   ├── agent.py   # 项目分析 Agent
│   │   │   └── config.py  # Agent 配置
│   │   └── deepresearch/
│   │       ├── agent.py   # 深度研究 Agent
│   │       ├── config.py  # Agent 配置
│   │       ├── files/
│   │       │   └── research_notes/  # 研究笔记临时目录
│   │       └── prompts/
│   │           ├── lead_agent.py     # Lead Agent prompt
│   │           ├── researcher.py     # Researcher prompt
│   │           └── notion_writer.py  # NotionWriter prompt
│   └── core/
│       ├── logging.py     # 日志工具
│       └── task_registry.py  # 任务 ID 生成
└── logs/                  # 运行日志目录
```
