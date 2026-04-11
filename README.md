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

## 启动命令

### 前端

```bash
cd frontend
npm run dev
```

### 后端

```bash
cd ..
python -m uvicorn backend.src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker (PostgreSQL)

```bash
docker run -d --name postgres -e POSTGRES_USER=vitacare -e POSTGRES_PASSWORD=vitacare -e POSTGRES_DB=logfix_ai -p 5432:5432 postgres:16
```
