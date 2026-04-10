# Quickstart: 日志文件切分

**Branch**: `001-log-split`
**Date**: 2026-04-10

## 环境要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Windows 10+

## 后端设置

### 1. 安装依赖

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `backend/.env` 文件：

```env
DATABASE_URL=postgresql://user:password@localhost:5432/logfix
LOG_DIR=./log
LOG_LEVEL=INFO
MAX_FILE_SIZE=209715200
```

### 3. 初始化数据库

```powershell
python -m src.db.init
```

### 4. 启动后端服务

```powershell
uvicorn src.main:app --reload --port 8000
```

API 文档地址: http://localhost:8000/docs

## 前端设置

### 1. 安装依赖

```powershell
cd frontend
npm install
```

### 2. 启动开发服务器

```powershell
npm run dev
```

访问地址: http://localhost:5173

## 启动顺序

1. 确保 PostgreSQL 已启动
2. 启动后端服务 (端口 8000)
3. 启动前端服务 (端口 5173)
4. 打开浏览器访问 http://localhost:5173

## 验证部署

### 后端健康检查

```bash
curl http://localhost:8000/api/health
```

### 前端连接测试

打开浏览器控制台，确认无跨域错误。

## 常见问题

### 数据库连接失败

确保 PostgreSQL 已启动且 `DATABASE_URL` 正确。

### 前端无法访问 API

确认后端已启动且 CORS 配置正确。

### 文件上传失败

检查 `MAX_FILE_SIZE` 配置和磁盘空间。
