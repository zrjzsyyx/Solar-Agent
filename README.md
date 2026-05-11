# Solar-Agent — 光伏电站智能运维 Agent

基于 LangChain + LangGraph 构建的光伏运维 AI Agent，自动分析告警、回答运维问题、生成运营报表。

## 架构

```
锦浪云 API → 数据后端（异常检测 + 数据采集）
                ↓
        Agent 后端（本仓库）← DeepSeek LLM
                ↓
        前端（H5 对话界面）
```

## 功能

| 流程 | 说明 |
|------|------|
| **告警分析** | 定时轮询数据后端，发现新告警 → LLM 深度分析根因 → 生成处理建议 → SSE 推送 |
| **智能问答** | 用户提问 → 意图分类 → 调用数据后端 API 查告警/逆变器/电站 → 流式生成回答 |
| **自动报表** | 手动/定时触发 → 汇总周期内告警和电站数据 → LLM 生成结构化周报/月报 |

## 技术栈

| 层 | 技术 |
|----|------|
| Agent 框架 | LangChain + LangGraph |
| LLM | DeepSeek（可切换通义千问等） |
| API 服务 | FastAPI + uvicorn |
| 数据通信 | httpx + SSE |
| 前端 | 原生 HTML/CSS/JS + marked.js |

## 项目结构

```
pv_agent/
├── backend/
│   ├── src/
│   │   ├── main.py                  # FastAPI 入口 + 告警轮询
│   │   ├── config.py                # 配置管理
│   │   ├── api/
│   │   │   ├── agent_routes.py      # /api/agent/qa, /api/agent/qa/stream, /api/agent/report/generate
│   │   │   ├── sse_routes.py        # /api/sse/agent-alerts
│   │   │   └── health_routes.py     # /api/health
│   │   ├── agent/
│   │   │   ├── graphs/              # LangGraph 状态图（alert / qa / report）
│   │   │   ├── state/               # 状态定义
│   │   │   └── prompts/             # 提示词模板
│   │   ├── tools/                   # @tool 工具函数（9个）
│   │   ├── services/                # 数据后端客户端 + 告警轮询
│   │   ├── models/                  # Pydantic 数据模型
│   │   └── utils/                   # LLM 工厂 + SSE 管理器
│   └── requirements.txt
├── frontend/
│   ├── index.html                   # 单页对话界面
│   ├── css/app.css
│   └── js/
│       ├── api.js                   # API 封装
│       └── chat.js                  # 对话组件（SSE + Markdown）
└── docs/
```

## 快速启动

### 1. 安装依赖

```bash
cd pv_agent/backend
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`：

```env
DEEPSEEK_API_KEY=你的DeepSeek密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
DATA_BACKEND_URL=https://solar-system-mon.preview.aliyun-zeabur.cn
AGENT_PORT=9000
ALERT_POLL_INTERVAL_SEC=60
```

### 3. 启动

```bash
uvicorn src.main:app --host 0.0.0.0 --port 9000 --reload
```

### 4. 访问

浏览器打开 `http://localhost:9000`

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | 前端对话界面 |
| `GET` | `/api/health` | 健康检查 |
| `POST` | `/api/agent/qa` | 问答（同步） |
| `GET` | `/api/agent/qa/stream?q=问题` | 问答（SSE 流式） |
| `POST` | `/api/agent/report/generate` | 生成报表 |
| `GET` | `/api/sse/agent-alerts` | 订阅 Agent 告警推送 |
