# LogFix AI PRD

本仓库包含 `LogFix AI` 的产品需求文档、MVP 拆解和按会话工作包组织的需求卡。

## 目录

- [docs/logfix-ai-prd/README.md](D:\code\test\docs\logfix-ai-prd\README.md)
- [docs/logfix-ai-prd/01-prd.md](D:\code\test\docs\logfix-ai-prd\01-prd.md)
- [docs/logfix-ai-prd/02-mvp-breakdown.md](D:\code\test\docs\logfix-ai-prd\02-mvp-breakdown.md)
- [docs/logfix-ai-prd/03-delivery-plan.md](D:\code\test\docs\logfix-ai-prd\03-delivery-plan.md)

## 使用方式

- 阅读 PRD：查看 `docs/logfix-ai-prd/01-prd.md`
- 规划 MVP：查看 `docs/logfix-ai-prd/02-mvp-breakdown.md`
- 按工作包推进：查看 `docs/logfix-ai-prd/requirements/README.md`

## 开发环境启动

### 前置依赖

```bash
# Python 虚拟环境
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows PowerShell

# 安装依赖
pip install -r requirements.txt

# Node.js 依赖
cd frontend
npm install
```

### 启动服务

**后端** (端口 8000):

```bash
cd backend
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**前端** (端口 5173):

```bash
cd frontend
npm run dev
```

### 环境变量配置

在项目根目录创建 `.env` 文件：

```bash
# 数据库
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/logfix_ai

# MiniMax API
MINIMAX_API_KEY=your_api_key_here
MINIMAX_API_HOST=https://api.minimaxaxi.com/v1

# AI 配置
AI_MAX_CONCURRENT=5
AI_BATCH_SIZE=20
```

### API 文档

启动后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
