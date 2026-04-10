# Quickstart: 日志分类与结构化存储

**Branch**: `002-short-name-structured`
**Date**: 2026-04-11

## 环境准备

### 1. 安装依赖

**后端**:
```bash
cd backend
python -m venv venv
venv\\Scripts\\activate  # Windows
pip install -r requirements.txt
```

**requirements.txt**:
```
fastapi>=0.109.0
uvicorn>=0.27.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.9
loguru>=0.7.2
pydantic>=2.5.0
python-dotenv>=1.0.0
langchain>=0.1.0
langchain-anthropic>=0.1.0
anthropic>=0.18.0
```

**前端**:
```bash
cd frontend
npm install
```

### 2. 环境配置

创建 `backend/.env`:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/logfix
LOG_DIR=./log
LOG_LEVEL=INFO
MINIMAX_API_KEY=your-api-key
MINIMAX_API_HOST=https://api.minimaxi.com/anthropic
```

### 3. 数据库初始化

```bash
cd backend
python -c "from src.db.session import init_db; init_db()"
```

---

## 快速启动

### 后端服务

```bash
cd backend
uvicorn src.main:app --reload --port 8000
```

### 前端服务

```bash
cd frontend
npm run dev
```

### 访问

- 前端: http://localhost:5173
- 后端 API: http://localhost:8000/api
- API 文档: http://localhost:8000/docs

---

## 基本使用流程

### 1. 上传日志文件

使用 001-log-split 的文件上传功能，上传日志文件并切分。

### 2. 分类和存储

调用分类接口，对切分后的日志进行分类和去重：

```bash
curl -X POST http://localhost:8000/api/classify \\
  -H "Content-Type: application/json" \\
  -d '{
    "logs": [
      "2024-01-01 10:00:00 ERROR java.lang.NullPointerException: Cannot invoke method on null object at line 10",
      "2024-01-01 10:00:01 ERROR java.lang.NullPointerException: Cannot invoke method on null object at line 20"
    ],
    "mode": "rule_engine"
  }'
```

### 3. 查看日志列表

```bash
curl "http://localhost:8000/api/logs?page=1&page_size=50"
```

### 4. 配置解析规则

```bash
# 创建规则
curl -X POST http://localhost:8000/api/rules \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Python异常提取",
    "rule_type": "regex",
    "pattern": "(\\w+Error): (.+)",
    "priority": 5,
    "enabled": true
  }'
```

### 5. 配置忽略规则

```bash
# 创建忽略规则
curl -X POST http://localhost:8000/api/ignore-rules \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "忽略连接超时",
    "match_type": "contains",
    "pattern": "Connection timeout",
    "enabled": true
  }'
```

---

## AI 模式使用

### 配置 MiniMax API

在 `backend/.env` 中配置：

```env
MINIMAX_API_KEY=your-minimax-api-key
MINIMAX_API_HOST=https://api.minimaxi.com/anthropic
```

### 调用 AI 模式

```bash
curl -X POST http://localhost:8000/api/classify \\
  -H "Content-Type: application/json" \\
  -d '{
    "logs": [
      "2024-01-01 10:00:00 ERROR Failed to connect to database at line 45",
      "2024-01-01 10:00:02 ERROR Connection timeout after 30s"
    ],
    "mode": "ai"
  }'
```

AI 将自动：
1. 分析日志语义
2. 分类日志类型
3. 归一化错误消息（去除参数）
4. 判断重复日志

---

## 验证清单

- [ ] 后端服务启动成功 (http://localhost:8000/docs 可访问)
- [ ] 前端服务启动成功 (http://localhost:5173 可访问)
- [ ] 数据库连接正常
- [ ] 日志文件正常输出到 `/log` 目录
- [ ] 规则引擎模式正常工作
- [ ] AI 模式正常工作（配置 API Key 后）
- [ ] 规则 CRUD 操作正常
- [ ] 忽略规则 CRUD 操作正常
