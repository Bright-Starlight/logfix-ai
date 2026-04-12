# Quickstart: AI 结构化工具调用与流式输出优化

**Branch**: `004-ai-tool-call-streaming`

## 开发环境准备

```bash
# 1. 安装依赖
cd backend
pip install openai sse-starlette

# 2. 配置环境变量
export MINIMAX_API_KEY=your_api_key
export MINIMAX_API_HOST=https://api.minimaxi.com/v1
```

## 启动服务

```bash
cd backend
uvicorn src.main:app --reload
```

服务启动时自动预加载模型，日志显示: `模型预加载完成, model=MiniMax-M2.7`

## API 调用示例

### SSE 流式分类

```python
import sseclient
import requests

response = requests.post(
    "http://localhost:8000/api/classify/stream",
    json={"logs": ["ERROR at line 10", "INFO connected"]},
    stream=True
)

client = sseclient.SSEClient(response)
for event in client.events():
    print(f"Event: {event.event}, Data: {event.data}")
```

## 测试验证

```bash
# 单元测试
cd backend
pytest tests/unit/test_ai_analyzer.py -v

# 集成测试
pytest tests/integration/test_streaming.py -v
```

## 前端集成

```typescript
const eventSource = new EventSource('/api/classify/stream', {
  method: 'POST',
  body: JSON.stringify({ logs: [...] })
});

eventSource.addEventListener('progress', (e) => {
  const { processed, total } = JSON.parse(e.data);
  updateProgressBar(processed, total);
});

eventSource.addEventListener('result', (e) => {
  const result = JSON.parse(e.data);
  displayResult(result);
});
```
