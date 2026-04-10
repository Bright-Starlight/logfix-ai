# Research: 日志文件切分

**Branch**: `001-log-split`
**Date**: 2026-04-10
**Status**: Complete

## 技术选型研究

### 1. Python 后端框架

**选择**: FastAPI

| 方案 | 优点 | 缺点 |
|------|------|------|
| FastAPI | 异步、高性能、自动文档、类型提示 | 学习曲线 |
| Flask | 简单、轻量 | 同步为主，无自动文档 |
| Django | 全功能、成熟 | 过于重量级 |

**结论**: FastAPI 的异步特性适合大文件流式处理场景。

### 2. 前端框架

**选择**: React + Vite

| 方案 | 优点 | 缺点 |
|------|------|------|
| React + Vite | 组件化、HMR快、生态丰富 | 需要构建步骤 |
| Vue | 上手简单、文档友好 | 生态较小 |
| 原生JS | 无需构建 | 难以维护 |

**结论**: React 生态成熟，Vite 提供极快的开发体验。

### 3. 数据库与 ORM

**选择**: PostgreSQL + SQLAlchemy

| 方案 | 优点 | 缺点 |
|------|------|------|
| PostgreSQL + SQLAlchemy | 关系型、JSON支持、成熟ORM | 需要额外学习 |
| SQLite | 零配置、轻量 | 并发支持弱 |
| MongoDB | 文档型、灵活 | 不适合结构化数据 |

**结论**: PostgreSQL 的 JSON 支持便于存储变长切分结果。

### 4. 大文件处理方案

**选择**: 前端分片上传 + 后端流式处理

| 方案 | 优点 | 缺点 |
|------|------|------|
| 前端分片 | 可靠性高、可断点续传 | 前端复杂度增加 |
| 流式读取 | 内存占用低 | 实现复杂度 |
| 整体上传 | 简单 | 内存溢出风险 |

**实现要点**:
- 前端使用 File.slice() 分片
- 后端使用 StreamingResponse 流式写入
- 切分过程逐行处理，避免全量加载

### 5. 文件编码检测

**选择**: chardet / charset-normalizer

| 方案 | 优点 | 缺点 |
|------|------|------|
| chardet | C扩展、准确率高 | Python2遗留API |
| charset-normalizer | 纯Python、活跃维护 | 略慢 |
| 内置codec | 无需依赖 | 不够智能 |

**结论**: charset-normalizer 活跃维护，纯Python实现。

### 6. 日志框架

**选择**: Python logging（宪法要求）

- 使用标准 logging 模块
- 配置 FileHandler 输出到 `/log` 目录
- 使用 TimedRotatingFileHandler 实现日志轮转

## 架构设计决策

### 决策 1: API 设计

```
POST   /api/upload          # 上传文件
GET    /api/files/{id}      # 获取文件预览
POST   /api/split           # 执行切分
GET    /api/sessions/{id}   # 获取切分状态
GET    /api/results/{id}    # 获取切分结果
```

### 决策 2: 数据模型

- LogFile: 上传文件元信息
- SplitSession: 切分任务会话
- SplitResult: 切分结果片段

### 决策 3: 前端状态管理

- 使用 React useState/useReducer 管理本地状态
- 使用 React Query 管理服务端状态
- 无需 Redux（复杂度不必要）

## 结论

所有技术选型已完成，无 NEEDS CLARIFICATION。
