# Data Model: 日志分类与结构化存储

**Branch**: `002-short-name-structured`
**Date**: 2026-04-11

## Entity Relationship

```
LogCategory (1) ─────< (N) LogEntry
    │
    │
LogEntry (1) ─────< (N) LogStatistics

ParseRule (1) ─────< (N) LogEntry (使用规则引擎时)

IgnoreRule (1) ─────< (N) LogEntry (跳过记录)
```

---

## Entity: LogEntry

表示一条已分类的日志记录。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 记录唯一标识 |
| original_message | TEXT | NOT NULL | 原始日志消息 |
| normalized_message | VARCHAR(500) | NOT NULL, INDEX | 归一化后的错误消息（去除参数） |
| stack_trace | TEXT | | 堆栈跟踪信息（保留完整堆栈便于调试） |
| category_id | UUID | FK → LogCategory | 所属分类 |
| error_type | VARCHAR(100) | INDEX | 错误类型（如 NullPointerException） |
| extracted_params | JSONB | | 提取的参数 {key: value} |
| log_level | VARCHAR(20) | INDEX | 日志级别（INFO/WARNING/ERROR） |
| occurrence_count | INTEGER | DEFAULT 1 | 累计发生次数 |
| first_seen_at | TIMESTAMP | NOT NULL | 首次出现时间 |
| last_seen_at | TIMESTAMP | NOT NULL | 最后出现时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**Indexes**:
- `idx_normalized_message` ON normalized_message
- `idx_category_id` ON category_id
- `idx_error_type` ON error_type
- `idx_log_level` ON log_level
- `idx_created_at` ON created_at

---

## Entity: LogCategory

表示日志分类。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 分类唯一标识 |
| name | VARCHAR(100) | UNIQUE, NOT NULL | 分类名称 |
| description | TEXT | | 分类描述 |
| color | VARCHAR(7) | | 展示颜色（#RRGGBB） |
| sort_order | INTEGER | DEFAULT 0 | 排序顺序 |
| is_system | BOOLEAN | DEFAULT FALSE | 是否系统预置 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**预置分类**:
| name | description | color |
|------|-------------|-------|
| 异常错误 | Java/Python/JS 等异常 | #EF4444 |
| 警告 | WARNING 级别日志 | #F59E0B |
| 信息 | INFO 级别日志 | #3B82F6 |
| 调试 | DEBUG 级别日志 | #6B7280 |
| 致命错误 | FATAL/CRITICAL 级别 | #7F1D1D |

---

## Entity: ParseRule

表示用户编写的解析规则（规则引擎模式）。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 规则唯一标识 |
| name | VARCHAR(100) | NOT NULL | 规则名称 |
| description | TEXT | | 规则描述 |
| rule_type | VARCHAR(20) | NOT NULL | 规则类型：regex / code |
| pattern | TEXT | | 正则表达式（regex 类型） |
| code | TEXT | | Python 代码片段（code 类型） |
| group_index | INTEGER | DEFAULT 0 | 提取分组索引 |
| priority | INTEGER | DEFAULT 0 | 优先级（数字越大越先执行） |
| enabled | BOOLEAN | DEFAULT TRUE | 是否启用 |
| is_system | BOOLEAN | DEFAULT FALSE | 是否系统预置 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**Indexes**:
- `idx_enabled_priority` ON enabled, priority DESC

---

## Entity: IgnoreRule

表示忽略规则。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 规则唯一标识 |
| name | VARCHAR(100) | NOT NULL | 规则名称 |
| match_type | VARCHAR(20) | NOT NULL | 匹配类型：contains / regex / exact |
| pattern | VARCHAR(500) | NOT NULL | 匹配模式 |
| description | TEXT | | 规则描述 |
| enabled | BOOLEAN | DEFAULT TRUE | 是否启用 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**Indexes**:
- `idx_enabled` ON enabled

---

## Entity: LogStatistics

表示日志统计汇总。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 统计唯一标识 |
| date | DATE | NOT NULL | 统计日期 |
| category_id | UUID | FK → LogCategory | 分类ID |
| entry_count | INTEGER | NOT NULL, DEFAULT 0 | 日志条目数 |
| unique_error_count | INTEGER | NOT NULL, DEFAULT 0 | 去重后唯一错误数 |
| total_occurrence | INTEGER | NOT NULL, DEFAULT 0 | 累计发生次数 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**Indexes**:
- `idx_date_category` ON date, category_id (UNIQUE)

---

## Validation Rules

1. **ParseRule.code** 执行时必须：
   - 禁止导入危险模块（os, sys, subprocess, etc.）
   - 禁止访问文件系统
   - 超时限制 1 秒

2. **IgnoreRule.pattern** 必须：
   - 正则类型时通过 `re.compile` 验证语法
   - 包含类型时最小长度 2 字符

3. **LogEntry.normalized_message** 计算规则：
   - 去除尾随空白
   - 替换数字序列为 `*`
   - 替换文件路径为文件名
