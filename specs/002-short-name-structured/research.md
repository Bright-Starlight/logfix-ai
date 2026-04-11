# Research: 日志分类与结构化存储

**Branch**: `002-short-name-structured`
**Date**: 2026-04-11

## Decision 1: AI 接入方式（LangChain + MiniMax）

### 选择
使用 LangChain + Anthropic SDK 接入 MiniMax-M2.7 模型

### 理由
- MiniMax 提供 Anthropic API 兼容接口 (`https://api.minimaxi.com/anthropic`)
- 可直接使用 `anthropic.Anthropic` 客户端，指定 `base_url` 即可
- LangChain 的 `ChatAnthropic` 或 `AnthropicLLM` 可复用此配置
- MiniMax-M2.7 在编程、日志分析等生产力场景表现优异

### 替代方案考虑
- **直接调用 REST API**：需要自行处理流式输出和错误重试
- **OpenAI SDK + OpenRouter**：可作为备选，但配置更复杂

### 实现方式
```python
from langchain_anthropic import ChatAnthropic
import anthropic

client = anthropic.Anthropic(
    base_url="https://api.minimaxi.com/anthropic",
    api_key="your-api-key"
)

llm = ChatAnthropic(
    model="MiniMax-M2.7",
    anthropic_api_key="your-api-key",
    anthropic_api_url="https://api.minimaxi.com/anthropic"
)
```

---

## Decision 2: 规则引擎设计

### 选择
用户编写的解析规则存储为 JSON，包含规则名称、正则表达式或 Python 代码片段

### 理由
- 正则表达式适合简单模式匹配
- Python 代码片段适合复杂逻辑
- JSON 格式便于存储和版本管理
- 可复用现有 PostgreSQL 数据库

### 规则数据结构
```json
{
  "name": "Java异常提取",
  "type": "regex",
  "pattern": "java\\.lang\\.(\\w+Exception): (.+)",
  "group_index": 1,
  "enabled": true
}
```

或代码片段：
```json
{
  "name": "自定义解析",
  "type": "code",
  "code": "def parse(line):\\n    if 'error' in line.lower():\\n        return {'type': 'error', 'msg': line.strip()}\\n    return None",
  "enabled": true
}
```

### 规则执行机制
- **正则规则**：使用 `re.match` 或 `re.search`
- **代码规则**：使用 `eval` 执行（沙箱限制）
- 规则按优先级顺序执行，首次匹配即返回结果

---

## Decision 3: AI 模式 Prompt 设计

### 选择
设计结构化 Prompt，引导 AI 输出 JSON 格式的分类和去重结果

### Prompt 模板
```
你是一个日志分析助手。请分析以下日志条目，进行分类和去重。

日志条目：
{log_entries}

请以 JSON 格式输出分析结果：
{{
  "classifications": [
    {{
      "original_index": 0,
      "category": "异常错误",
      "error_type": "NullPointerException",
      "normalized_message": "Null pointer at line *",
      "extracted_params": {{"line": "10"}}
    }}
  ],
  "duplicates": [
    {{
      "representative_index": 0,
      "duplicate_indices": [3, 7]
    }}
  ]
}}

注意：
1. 相同错误消息（仅参数不同）应归为同一组
2. normalized_message 应去除参数，保留错误模式
3. extracted_params 应提取所有参数
```

### 理由
- 明确的输出格式要求便于解析
- 分类和去重信息一起返回，减少 API 调用
- 参数提取便于后续分析

---

## Decision 4: 去重算法

### 规则引擎模式
1. **消息归一化**：去除数字、文件名等动态参数
   - 正则替换：`\d+` → `*`
   - 路径去除：`/home/user/file.py:10` → `file.py:*`
2. **哈希匹配**：归一化后计算哈希，相同哈希视为相同错误
3. **模糊匹配**（可选）：使用编辑距离判断相似度

### AI 模式
- AI 自动理解语义相似性
- Prompt 中明确要求"相同错误消息（仅参数不同）应归为同一组"

### 去重流程
```
输入日志 → 规则引擎模式?
  ├─ 是 → 归一化 → 哈希匹配 → 查询DB是否存在
  │         ├─ 存在 → 标记为重复，更新统计
  │         └─ 不存在 → 新增记录
  └─ 否 → AI模式 → 调用AI → 解析结果 → 更新DB
```

---

## 总结

| 决策项 | 最终选择 |
|--------|----------|
| AI 接入 | LangChain + Anthropic SDK → MiniMax-M2.7 |
| 规则存储 | PostgreSQL JSON 字段 |
| 规则执行 | re 正则 + eval 代码（沙箱） |
| AI Prompt | 结构化 JSON 输出 |
| 去重算法 | 规则引擎：归一化哈希；AI：语义理解 |
