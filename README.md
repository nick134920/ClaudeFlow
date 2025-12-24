# New Project AutoAnalyse

基于 Claude Agent SDK 构建的新项目自动分析系统，能够自动抓取 URL 内容、进行 AI 智能分析，并将结果存储到 Notion。

## 项目说明

### 功能特性

- **URL 智能抓取**：支持任意 URL，特别优化了 GitHub 项目的元数据提取（Stars、Fork、最后提交时间等）
- **AI 深度分析**：使用 Claude AI 模型对内容进行智能分析，生成结构化的中文摘要
- **Notion 自动归档**：分析结果自动创建为 Notion 页面，支持多层级思维导图格式
- **异步任务处理**：基于 FastAPI BackgroundTasks 实现请求即返回，后台异步执行
- **完整日志追踪**：详细记录每个任务的执行过程、工具调用、耗时和成本

### 技术架构

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

### 技术栈

| 类型 | 技术 |
|------|------|
| 语言 | Python 3.11+ |
| Web 框架 | FastAPI + Uvicorn |
| AI 引擎 | Claude Agent SDK |
| MCP 服务 | Firecrawl（网页抓取）、Notion（页面管理） |
| 配置管理 | YAML |

## 部署说明

### 环境要求

- Python 3.11 或更高版本
- Node.js（用于运行 MCP 服务器）
- Firecrawl API Key（从 [firecrawl.dev](https://firecrawl.dev) 获取）
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
```

4. **启动服务**

```bash
python run.py
```

服务将在 `http://0.0.0.0:8000` 启动。

### API 使用

**请求分析任务**

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
new-project-autoanalyse/
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
│   │   └── newprojectanalyse/
│   │       ├── agent.py   # 分析 Agent 实现
│   │       └── config.py  # Agent 配置
│   └── core/
│       ├── logging.py     # 日志工具
│       └── task_registry.py  # 任务 ID 生成
└── logs/                  # 运行日志目录
```
