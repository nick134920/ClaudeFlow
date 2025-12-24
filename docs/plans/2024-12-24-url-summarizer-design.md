# URL 总结服务设计方案

## 概述

基于 Claude Agent SDK 开发的 HTTP 服务，接收 URL 后自动抓取网页内容、生成 Markdown 总结，并创建 Notion Page。

## 技术选型

| 组件 | 选择 |
|------|------|
| Web 框架 | FastAPI |
| Agent SDK | claude-agent-sdk (Python) |
| 网页抓取 | MCP Firecrawl |
| 笔记存储 | MCP Notion |
| 配置管理 | .env 文件 |

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      HTTP Request                            │
│          POST /summarize?api_key=xxx                         │
│          Body: {"url": "https://example.com"}               │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Server                            │
│  1. 验证 api_key                                             │
│  2. 验证 url 格式                                            │
│  3. 启动后台任务 (BackgroundTasks)                           │
│  4. 立即返回 {"success": true}                               │
└─────────────────────┬───────────────────────────────────────┘
                      │ (后台异步执行)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                 Claude Agent SDK                             │
│  MCP Firecrawl → 抓取内容                                    │
│  Claude        → 生成标题 + Markdown 总结                    │
│  MCP Notion    → 创建 Page                                   │
└─────────────────────────────────────────────────────────────┘
```

## 项目结构

```
new-project-autoanalyse/
├── .env                    # 配置文件
├── main.py                 # FastAPI 入口 + 路由
├── agent.py                # Claude Agent SDK 调用逻辑
└── requirements.txt        # 依赖
```

## 配置项

**.env 文件：**
```
API_KEY=your-secret-key
NOTION_PARENT_PAGE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

## API 设计

### POST /summarize

**请求：**
- Query 参数: `api_key` (必填)
- Body: `{"url": "https://example.com"}`

**响应：**
- 成功: `{"success": true}`
- 失败: `{"success": false}`

**特点：**
- 立即返回，不等待 Agent 任务完成
- 后台异步执行抓取、总结、创建 Notion Page

## 核心流程

### main.py 处理流程

1. 检查 `api_key` 是否匹配配置
2. 验证 `url` 格式有效性
3. 添加后台任务
4. 立即返回响应

### agent.py 后台任务流程

1. 使用 MCP Firecrawl 抓取 URL 内容
2. Claude 生成简洁中文标题
3. Claude 将内容总结为 Markdown 格式
4. 使用 MCP Notion 在指定父页面下创建 Page

## 依赖

```
fastapi
uvicorn
python-dotenv
claude-agent-sdk
```

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| api_key 错误 | 返回 `{"success": false}` |
| url 格式无效 | 返回 `{"success": false}` |
| 后台 Agent 执行失败 | 静默失败 |

## 启动命令

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
