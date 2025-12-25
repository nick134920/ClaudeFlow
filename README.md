# Claude Agent SDK 应用集合

基于 Claude Agent SDK 构建的多 Agent 应用系统，提供 HTTP API 接口，支持与 iOS/Mac 快捷指令无缝集成。

## 功能模块

### NewProjectAnalyse - 新项目分析

自动抓取 URL 内容、进行 AI 智能分析，并将结果存储到 Notion。

- **URL 智能抓取**：支持任意 URL，特别优化 GitHub 项目元数据提取
- **AI 深度分析**：使用 Claude 模型生成结构化中文摘要
- **Notion 自动归档**：分析结果自动创建为 Notion 页面

### DeepResearch - 深度研究

多 Agent 协作的深度研究系统，使用 Tavily 进行网络搜索。

- **多 Agent 协作**：Lead Agent 协调任务分解，Researcher 并行搜索
- **结构化输出**：使用 JSON Schema 强制格式化，自动创建 Notion 页面
- **Tavily 搜索**：支持配置搜索深度和结果数量

### QuickNote - 快速笔记

轻量级笔记 API，将内容追加到指定 Notion 页面。

- **即时写入**：同步执行，立即返回结果
- **简单易用**：单一接口，无需复杂配置
- **快捷指令友好**：适合 iOS/Mac 快捷指令随时记录灵感

## 技术架构

```
客户端请求 (curl / iOS 快捷指令 / 浏览器)
    ↓
FastAPI 路由 → API Key 验证 → 任务 ID 生成
    ↓
后台异步执行 (BackgroundTasks)
    ↓
Agent 执行
    ├── MCP 工具调用 (Firecrawl / Tavily)
    ├── Claude Agent SDK 多轮对话
    └── 结构化输出 (JSON Schema)
    ↓
Notion SDK 创建页面
    ↓
日志记录完成
```

**技术栈**

| 类型 | 技术 |
|------|------|
| 语言 | Python 3.11+ |
| Web 框架 | FastAPI + Uvicorn |
| AI 引擎 | Claude Agent SDK |
| MCP 服务 | Firecrawl（网页抓取）、Tavily（网络搜索） |
| 存储 | Notion SDK（直接 API 调用） |

## 快速开始

### 环境要求

- Python 3.11+
- Node.js（运行 MCP 服务器）
- API Keys：
  - Firecrawl: [firecrawl.dev](https://firecrawl.dev)
  - Tavily: [tavily.com](https://tavily.com)
  - Notion: [Notion Integrations](https://www.notion.so/my-integrations)

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd claude-agent-sdk

# 安装依赖
pip install -r requirements.txt

# 配置
cp config.yaml.example config.yaml
# 编辑 config.yaml 填入 API Keys
```

### 配置说明

```yaml
# config.yaml
api_key: your-secret-key        # 自定义 API 访问密钥
log_dir: logs
log_level: INFO

# NewProjectAnalyse 配置
newprojectanalyse:
  model: claude-sonnet-4-20250514
  max_turns: 15
  notion:
    token: your-notion-token
    parent_page_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  mcp_servers:
    firecrawl:
      type: stdio
      command: npx
      args: ["-y", "firecrawl-mcp"]
      env:
        FIRECRAWL_API_KEY: your-firecrawl-key

# QuickNote 配置
quicknote:
  notion:
    token: your-notion-token
    page_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx  # 写入笔记的目标页面

# DeepResearch 配置
deepresearch:
  model: claude-sonnet-4-20250514
  max_turns: 20
  notion:
    token: your-notion-token
    parent_page_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  tavily:
    search_depth: advanced    # basic | advanced
    max_results: 10
  mcp_servers:
    tavily:
      type: stdio
      command: npx
      args: ["-y", "tavily-mcp@latest"]
      env:
        TAVILY_API_KEY: your-tavily-key
```

### 启动服务

```bash
python run.py
# 服务运行在 http://0.0.0.0:8000
```

## API 接口

### POST /newprojectanalyse

分析指定 URL 的内容并保存到 Notion。

```bash
curl -X POST "http://localhost:8000/newprojectanalyse?api_key=your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://github.com/example/project"}'
```

**响应**
```json
{"success": true, "task_id": "newprojectanalyse_251224_14_30_00"}
```

### POST /deepresearch

对指定主题进行深度研究并保存到 Notion。

```bash
curl -X POST "http://localhost:8000/deepresearch?api_key=your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"topic":"2024年大语言模型发展趋势"}'
```

**响应**
```json
{"success": true, "task_id": "deepresearch_251225_11_30_00"}
```

### POST /quicknote

快速笔记 - 追加内容到指定 Notion 页面。

```bash
curl -X POST "http://localhost:8000/quicknote?api_key=your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"content":"这是一条快速笔记"}'
```

**响应**
```json
{"success": true, "message": "笔记已追加", "input": {"content": "这是一条快速笔记"}}
```

### GET /check-agent-health

检查 Agent 服务健康状态。

```bash
curl "http://localhost:8000/check-agent-health?api_key=your-api-key"
```

**响应**
```json
{"healthy": true, "response": "I am Claude...", "error": null}
```

## iOS / Mac 快捷指令集成

本项目 API 设计简洁，特别适合与 Apple 快捷指令配合使用。

### 使用场景

- **Safari 分享菜单**：浏览网页时直接分享到快捷指令，自动分析并存入 Notion
- **剪贴板 URL**：复制链接后运行快捷指令，自动提取并分析
- **Siri 语音触发**：语音输入研究主题，后台执行深度研究

### 创建快捷指令

#### 方式一：NewProjectAnalyse - 网页分析

1. 打开「快捷指令」App，点击「+」创建新快捷指令
2. 添加以下操作：

```
[接收] 共享表单输入 → URLs
    ↓
[变量] 设置变量「url」为「共享表单输入」
    ↓
[网络] 获取 URL 的内容
    URL: http://your-server:8000/newprojectanalyse?api_key=YOUR_API_KEY
    方法: POST
    请求体: JSON
    {
      "url": [url 变量]
    }
    ↓
[脚本] 获取词典值「success」
    ↓
[脚本] 如果「success」等于 true
    → 显示通知「任务已提交」
    否则
    → 显示通知「提交失败」
```

3. 在快捷指令设置中启用「在共享表单中显示」
4. 现在可以从 Safari 等 App 的分享菜单直接调用

#### 方式二：DeepResearch - 深度研究

1. 创建新快捷指令
2. 添加以下操作：

```
[输入] 请求输入 → 文本
    提示: 请输入研究主题
    ↓
[变量] 设置变量「topic」为「提供的输入」
    ↓
[网络] 获取 URL 的内容
    URL: http://your-server:8000/deepresearch?api_key=YOUR_API_KEY
    方法: POST
    请求体: JSON
    {
      "topic": [topic 变量]
    }
    ↓
[脚本] 获取词典值「task_id」
    ↓
[脚本] 显示通知
    标题: 研究任务已启动
    内容: [task_id]
```

3. 可添加到主屏幕或设置 Siri 语音触发

#### 方式三：QuickNote - 快速笔记

1. 创建新快捷指令
2. 添加以下操作：

```
[输入] 请求输入 → 文本
    提示: 输入笔记内容
    ↓
[变量] 设置变量「content」为「提供的输入」
    ↓
[网络] 获取 URL 的内容
    URL: http://your-server:8000/quicknote?api_key=YOUR_API_KEY
    方法: POST
    请求体: JSON
    {
      "content": [content 变量]
    }
    ↓
[脚本] 获取词典值「success」
    ↓
[脚本] 如果「success」等于 true
    → 显示通知「笔记已保存」
    否则
    → 显示通知「保存失败」
```

3. 可设置 Siri 语音触发，随时记录灵感

### 快捷指令配置要点

| 配置项 | 说明 |
|--------|------|
| URL | 替换为你的服务器地址，如 `http://192.168.1.100:8000` |
| api_key | 替换为 config.yaml 中设置的密钥 |
| 请求体类型 | 必须选择 JSON |
| 超时设置 | API 立即返回，无需长超时 |

### 网络配置注意事项

**局域网访问**
- 确保 iOS 设备与服务器在同一网络
- 服务器防火墙允许 8000 端口
- 使用服务器 IP 地址而非 localhost

**公网访问**
- 配置端口转发或使用反向代理（Nginx/Caddy）
- 强烈建议启用 HTTPS
- 使用强 API Key 并定期更换

**内网穿透方案**
- [Tailscale](https://tailscale.com)：零配置 VPN，推荐
- [Cloudflare Tunnel](https://www.cloudflare.com/products/tunnel/)：免费 HTTPS 隧道
- [frp](https://github.com/fatedier/frp)：自建内网穿透

### 进阶用法

**剪贴板 URL 分析**

```
[脚本] 获取剪贴板
    ↓
[文本] 匹配 URL 正则 (https?://[^\s]+)
    ↓
[网络] POST 到 /newprojectanalyse
```

**批量 URL 处理**

```
[输入] 请求输入 → 文本（多行 URL）
    ↓
[文本] 按行分割
    ↓
[重复] 对于每个 URL
    → POST 到 /newprojectanalyse
    → 等待 1 秒
    ↓
[显示] 完成通知
```

**定时研究任务（需自动化）**

```
[自动化] 每周一上午 9:00
    ↓
[文本] 预设主题列表
    ↓
[随机] 选择一个主题
    ↓
[网络] POST 到 /deepresearch
```

## 日志查看

```bash
# 请求日志
tail -f logs/2025-12-25/requests.log | jq

# 任务执行日志
tail -f logs/2025-12-25/tasks/deepresearch_*.log
```

日志目录结构：
```
logs/
└── 2025-12-25/
    ├── requests.log           # HTTP 请求日志 (JSON Lines)
    └── tasks/
        └── {task_id}.log      # 任务执行详情
```

## 生产部署

### 方式一：直接运行

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 方式二：Docker Compose

```bash
# 配置环境变量
cp .env.example .env
# 编辑 .env 填入必要变量

# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### Nginx 反向代理配置

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 项目结构

```
claude-agent-sdk/
├── run.py                      # 应用入口
├── config.yaml                 # 配置文件
├── config.yaml.example         # 配置示例
├── requirements.txt            # Python 依赖
├── Dockerfile                  # Docker 构建
├── docker-compose.yml          # Docker Compose
│
├── app/
│   ├── main.py                 # FastAPI 应用
│   ├── config.py               # 配置加载器
│   │
│   ├── api/
│   │   ├── routes.py           # API 路由
│   │   └── models.py           # 数据模型
│   │
│   ├── agents/
│   │   ├── base.py             # Agent 基类
│   │   ├── newprojectanalyse/
│   │   │   ├── agent.py        # 项目分析 Agent
│   │   │   └── config.py
│   │   └── deepresearch/
│   │       ├── agent.py        # 深度研究 Agent
│   │       ├── config.py
│   │       ├── schema.py       # 输出 JSON Schema
│   │       └── prompts/
│   │           ├── lead_agent.py
│   │           └── researcher.py
│   │
│   ├── services/
│   │   └── notion.py           # Notion SDK 封装
│   │
│   └── core/
│       ├── logging.py          # 日志系统
│       └── task_registry.py    # 任务 ID 生成
│
└── logs/                       # 运行日志
```

## 扩展开发

### 添加新 Agent

1. 在 `app/agents/` 下创建新目录
2. 实现继承 `BaseAgent` 的类
3. 覆盖必要方法：
   - `get_prompt(**kwargs)` - 返回提示词
   - `get_options()` - 返回 ClaudeAgentOptions
   - `process_structured_output()` 或 `process_final_output()` - 处理输出
4. 在 `app/api/routes.py` 添加新端点

### BaseAgent 钩子方法

```python
class MyAgent(BaseAgent):
    MODULE_NAME = "myagent"

    def get_prompt(self, **kwargs) -> str:
        return "你的提示词"

    def get_options(self) -> ClaudeAgentOptions:
        return ClaudeAgentOptions(
            model="claude-sonnet-4-20250514",
            max_turns=10,
            output_format=MY_JSON_SCHEMA,  # 强制结构化输出
        )

    async def process_structured_output(self, output: dict, **kwargs) -> None:
        # output 是 SDK 解析后的结构化数据
        # 直接使用，无需手动解析 JSON
        pass
```

## 许可证

MIT License
