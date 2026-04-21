# FastPPT API 文档

FastPPT 后端 API 完整参考文档，供前端开发使用。

**Base URL**: `http://localhost:8000`

**版本**: 1.0.0

---

## 目录

1. [检索 API](#检索-api)
2. [对话 API](#对话-api)
3. [生成 API](#生成-api)
4. [文件上传 API](#文件上传-api)
5. [文件下载 API](#文件下载-api)
6. [语音识别 API](#语音识别-api)
7. [监控 API](#监控-api)
8. [错误码说明](#错误码说明)

---

## 检索 API

### 1. 上传文档

上传文档到 RAGFlow 知识库进行索引。

**接口**: `POST /api/retrieval/upload`

**Content-Type**: `multipart/form-data`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 文档文件（PDF, DOCX, TXT, MD 等） |
| kb_id | string | 否 | 知识库 ID（不提供则使用环境变量默认值） |
| parser | string | 否 | 解析器类型：layout_aware（默认）, naive, qa, table |

**响应示例**:

```json
{
  "doc_id": "abc123def456",
  "status": "uploaded",
  "message": "文档 example.pdf 上传成功"
}
```

**curl 示例**:

```bash
curl -X POST http://localhost:8000/api/retrieval/upload \
  -F "file=@/path/to/document.pdf" \
  -F "parser=layout_aware"
```

**JavaScript fetch 示例**:

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('parser', 'layout_aware');

const response = await fetch('http://localhost:8000/api/retrieval/upload', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Document ID:', result.doc_id);
```

**错误响应**:

```json
{
  "detail": "文档上传失败: [错误信息]"
}
```

---

### 2. 搜索知识库

使用混合检索（向量 + 关键词）搜索知识库。

**接口**: `POST /api/retrieval/search`

**Content-Type**: `application/json`

**请求参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| query | string | 是 | - | 搜索查询文本 |
| kb_ids | string[] | 否 | [] | 知识库 ID 列表（空则使用默认） |
| top_k | integer | 否 | 5 | 返回结果数量（1-20） |
| similarity_threshold | float | 否 | 0.7 | 最小相似度阈值（0.0-1.0） |
| rerank | boolean | 否 | true | 是否使用重排序 |

**请求示例**:

```json
{
  "query": "机器学习的基本概念",
  "kb_ids": ["kb_123"],
  "top_k": 5,
  "similarity_threshold": 0.7,
  "rerank": true
}
```

**响应示例**:

```json
{
  "chunks": [
    {
      "content": "机器学习是人工智能的一个分支...",
      "score": 0.92,
      "doc_id": "doc_123",
      "doc_name": "AI基础.pdf"
    }
  ],
  "total": 5,
  "query": "机器学习的基本概念"
}
```

**curl 示例**:

```bash
curl -X POST http://localhost:8000/api/retrieval/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "机器学习的基本概念",
    "top_k": 5,
    "similarity_threshold": 0.7,
    "rerank": true
  }'
```

**JavaScript fetch 示例**:

```javascript
const response = await fetch('http://localhost:8000/api/retrieval/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: '机器学习的基本概念',
    top_k: 5,
    similarity_threshold: 0.7,
    rerank: true
  })
});

const result = await response.json();
console.log('Found chunks:', result.chunks.length);
```

---

### 3. 列出文档

获取知识库中所有文档的列表。

**接口**: `GET /api/retrieval/documents`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| kb_id | string | 否 | 知识库 ID（不提供则使用默认值） |

**响应示例**:

```json
{
  "documents": [
    {
      "doc_id": "doc_123",
      "name": "AI基础.pdf",
      "status": "indexed",
      "upload_time": "2026-04-21T10:30:00Z",
      "parser": "layout_aware",
      "chunk_count": 45
    }
  ],
  "total": 1,
  "kb_id": "kb_123"
}
```

**curl 示例**:

```bash
curl -X GET "http://localhost:8000/api/retrieval/documents?kb_id=kb_123"
```

**JavaScript fetch 示例**:

```javascript
const response = await fetch('http://localhost:8000/api/retrieval/documents?kb_id=kb_123');
const result = await response.json();
console.log('Total documents:', result.total);
```

---

### 4. 删除文档

从知识库中永久删除文档及其所有索引。

**接口**: `DELETE /api/retrieval/documents/{doc_id}`

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| doc_id | string | 是 | 文档 ID |

**响应示例**:

```json
{
  "success": true,
  "doc_id": "doc_123",
  "message": "文档 doc_123 删除成功"
}
```

**curl 示例**:

```bash
curl -X DELETE http://localhost:8000/api/retrieval/documents/doc_123
```

**JavaScript fetch 示例**:

```javascript
const response = await fetch('http://localhost:8000/api/retrieval/documents/doc_123', {
  method: 'DELETE'
});
const result = await response.json();
console.log('Deleted:', result.success);
```

---

## 对话 API

### POST /api/chat

智能对话接口，支持流式和非流式响应，可选 Agent 模式。

**Content-Type**: `application/json`

**请求参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| messages | array | 是 | - | 对话消息列表 |
| stream | boolean | 否 | false | 是否使用流式响应（SSE） |
| use_agent | boolean | 否 | false | 是否使用 Agent 模式（带工具调用） |
| session_id | string | 否 | null | 会话 ID（用于多轮对话） |

**messages 格式**:

```json
[
  { "role": "user", "content": "我想制作一个关于机器学习的课件" },
  { "role": "assistant", "content": "好的，请告诉我..." },
  { "role": "user", "content": "面向大学生，45分钟" }
]
```

**非流式响应示例**:

```json
{
  "reply": "好的，我将为您生成一个关于机器学习的课件...",
  "intent_ready": true,
  "intent": {
    "topic": "机器学习基础",
    "audience": "大学生",
    "duration": "45分钟",
    "key_points": ["监督学习", "无监督学习", "深度学习"]
  },
  "teaching_spec": {
    "topic": "机器学习基础",
    "audience": "大学生",
    "duration": "45分钟",
    "style": "学术",
    "key_points": ["监督学习", "无监督学习", "深度学习"],
    "unresolved_fields": []
  },
  "session_id": "sess_abc123"
}
```

**流式响应（SSE）**:

当 `stream: true` 时，返回 `text/event-stream` 格式：

```
data: {"chunk": "好的"}

data: {"chunk": "，我将"}

data: {"chunk": "为您生成"}

data: {"done": true, "intent_ready": true, "intent": {...}, "teaching_spec": {...}, "summary": "..."}
```

**curl 示例（非流式）**:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "我想制作一个关于Python的课件，面向初学者"}
    ],
    "stream": false,
    "use_agent": false
  }'
```

**JavaScript fetch 示例（非流式）**:

```javascript
const response = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    messages: [
      { role: 'user', content: '我想制作一个关于Python的课件，面向初学者' }
    ],
    stream: false,
    use_agent: false
  })
});

const result = await response.json();
console.log('Reply:', result.reply);
console.log('Intent ready:', result.intent_ready);
```

**JavaScript fetch 示例（流式 SSE）**:

```javascript
const eventSource = new EventSource('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    messages: [
      { role: 'user', content: '我想制作一个关于Python的课件' }
    ],
    stream: true
  })
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.chunk) {
    // 流式输出文本片段
    console.log('Chunk:', data.chunk);
  }
  
  if (data.done) {
    // 流式结束
    console.log('Intent ready:', data.intent_ready);
    console.log('Intent:', data.intent);
    eventSource.close();
  }
  
  if (data.error) {
    console.error('Error:', data.error);
    eventSource.close();
  }
};
```

**use_agent 参数说明**:

- `false`（默认）: 使用传统 LLM 对话模式
- `true`: 使用 Agent 模式，支持工具调用（RAG 检索、知识库查询等）

**Agent 模式特点**:

- 自动调用 RAG 检索工具获取相关知识
- 支持多轮对话上下文记忆
- 更智能的意图理解和补全

---

## 生成 API

### 1. 同步生成（已废弃）

**接口**: `POST /api/generate`

**说明**: 同步生成接口，仅用于向后兼容。推荐使用异步生成接口。

**请求参数**:

```json
{
  "intent": {
    "topic": "机器学习基础",
    "audience": "大学生",
    "duration": "45分钟",
    "key_points": ["监督学习", "无监督学习"]
  },
  "file_ids": []
}
```

**响应示例**:

```json
{
  "slides_json": { "pages": [...] },
  "docx": "abc12345_教案.docx",
  "message": "课件生成成功，共 15 页",
  "teaching_spec": {...},
  "block_summary": {...}
}
```

---

### 2. 启动异步生成

启动异步生成任务，立即返回 job_id。

**接口**: `POST /api/generate/start`

**Content-Type**: `application/json`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| intent | object | 是 | 课件生成意图（从对话 API 获取） |
| file_ids | string[] | 否 | 关联的文件 ID 列表 |

**请求示例**:

```json
{
  "intent": {
    "topic": "机器学习基础",
    "audience": "大学生",
    "duration": "45分钟",
    "style": "学术",
    "key_points": ["监督学习", "无监督学习", "深度学习"]
  },
  "file_ids": ["file_123", "file_456"]
}
```

**响应示例**:

```json
{
  "job_id": "abc12345"
}
```

**curl 示例**:

```bash
curl -X POST http://localhost:8000/api/generate/start \
  -H "Content-Type: application/json" \
  -d '{
    "intent": {
      "topic": "机器学习基础",
      "audience": "大学生",
      "duration": "45分钟",
      "key_points": ["监督学习", "无监督学习"]
    }
  }'
```

**JavaScript fetch 示例**:

```javascript
const response = await fetch('http://localhost:8000/api/generate/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    intent: {
      topic: '机器学习基础',
      audience: '大学生',
      duration: '45分钟',
      key_points: ['监督学习', '无监督学习']
    }
  })
});

const result = await response.json();
console.log('Job ID:', result.job_id);
```

---

### 3. 获取生成进度（SSE 流）

通过 SSE 流实时获取生成进度和结果。

**接口**: `GET /api/generate/{job_id}/stream`

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| job_id | string | 是 | 任务 ID（从 start 接口获取） |

**SSE 事件格式**:

```
data: {"progress": 10, "message": "正在检索知识库...", "done": false}

data: {"progress": 35, "message": "正在生成课件内容...", "done": false}

data: {"progress": 65, "message": "正在归一化页面内容块...", "done": false}

data: {"progress": 80, "message": "正在生成 Word 教案...", "done": false}

data: {"progress": 100, "message": "生成完成", "done": true, "slides_json": {...}, "docx": "abc12345_教案.docx", "teaching_spec": {...}, "block_summary": {...}}
```

**错误事件格式**:

```
data: {"progress": 35, "message": "生成失败: [错误信息]", "done": true, "error": "[错误详情]"}
```

**JavaScript EventSource 示例**:

```javascript
const jobId = 'abc12345'; // 从 start 接口获取
const eventSource = new EventSource(`http://localhost:8000/api/generate/${jobId}/stream`);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  console.log(`Progress: ${data.progress}% - ${data.message}`);
  
  if (data.done) {
    if (data.error) {
      console.error('Generation failed:', data.error);
    } else {
      console.log('Generation complete!');
      console.log('Slides:', data.slides_json);
      console.log('DOCX:', data.docx);
    }
    eventSource.close();
  }
};

eventSource.onerror = (error) => {
  console.error('SSE error:', error);
  eventSource.close();
};
```

**异步生成流程说明**:

1. 调用 `POST /api/generate/start` 获取 `job_id`
2. 使用 `job_id` 连接 `GET /api/generate/{job_id}/stream` SSE 流
3. 监听进度事件，更新 UI 进度条
4. 收到 `done: true` 事件后，获取生成结果
5. 使用 `docx` 字段的文件名调用下载接口

**进度阶段**:

- 10%: 正在检索知识库
- 35%: 正在生成课件内容
- 65%: 正在归一化页面内容块
- 80%: 正在生成 Word 教案
- 100%: 生成完成

---

## 文件上传 API

### POST /api/upload

上传文件（文档/图片/视频）并自动解析内容。

**接口**: `POST /api/upload`

**Content-Type**: `multipart/form-data`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 文件对象 |

**支持的文件类型**:

- 文档: `.pdf`, `.docx`, `.doc`, `.pptx`, `.ppt`, `.txt`, `.md`
- 图片: `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`
- 视频: `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`

**响应示例（文档）**:

```json
{
  "file_id": "abc12345",
  "filename": "example.pdf",
  "summary": "这是一份关于机器学习的文档...",
  "chunk_count": 25,
  "type": "doc"
}
```

**响应示例（图片）**:

```json
{
  "file_id": "img12345",
  "filename": "diagram.png",
  "summary": "这是一张展示神经网络结构的图表...",
  "chunk_count": 3,
  "type": "image"
}
```

**响应示例（视频）**:

```json
{
  "file_id": "vid12345",
  "filename": "lecture.mp4",
  "summary": "视频时长 300s，提取 10 帧，字幕 1500 字",
  "chunk_count": 15,
  "type": "video",
  "frames": [
    {
      "id": "frame_001",
      "timestamp": 30.5,
      "description": "讲师正在讲解机器学习概念",
      "save_path": "uploads/vid12345_frame_001.jpg"
    }
  ]
}
```

**curl 示例**:

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@/path/to/document.pdf"
```

**JavaScript fetch 示例**:

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8000/api/upload', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('File ID:', result.file_id);
console.log('Summary:', result.summary);
console.log('Chunks:', result.chunk_count);
```

**文件处理说明**:

- 文档: 提取文本并分块，自动添加到 RAG 知识库
- 图片: 使用多模态 LLM 生成描述，添加到知识库
- 视频: 提取关键帧、字幕，生成描述，添加到知识库

---

## 文件下载 API

### 1. 下载文件

下载生成的课件或教案文件。

**接口**: `GET /api/download/{filename}`

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| filename | string | 是 | 文件名（从生成接口获取） |

**响应**: 文件流（application/octet-stream）

**curl 示例**:

```bash
curl -O http://localhost:8000/api/download/abc12345_教案.docx
```

**JavaScript fetch 示例**:

```javascript
const filename = 'abc12345_教案.docx';
const response = await fetch(`http://localhost:8000/api/download/${filename}`);
const blob = await response.blob();

// 创建下载链接
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = filename;
a.click();
window.URL.revokeObjectURL(url);
```

---

### 2. 预览 PPT

获取 PPT 各页的缩略图预览。

**接口**: `GET /api/preview/{filename}`

**路径参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| filename | string | 是 | PPT 文件名 |

**响应示例**:

```json
{
  "slides": [
    {
      "page": 1,
      "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
    },
    {
      "page": 2,
      "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
    }
  ],
  "total": 15
}
```

**curl 示例**:

```bash
curl -X GET "http://localhost:8000/api/preview/abc12345_课件.pptx"
```

**JavaScript fetch 示例**:

```javascript
const filename = 'abc12345_课件.pptx';
const response = await fetch(`http://localhost:8000/api/preview/${filename}`);
const result = await response.json();

// 显示缩略图
result.slides.forEach(slide => {
  const img = document.createElement('img');
  img.src = slide.image;
  img.alt = `第 ${slide.page} 页`;
  document.body.appendChild(img);
});
```

---

## 语音识别 API

### POST /api/asr

将录音文件转换为文字（使用 Paraformer ASR）。

**接口**: `POST /api/asr`

**Content-Type**: `multipart/form-data`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 音频文件（WAV, MP3, WebM） |

**响应示例**:

```json
{
  "text": "我想制作一个关于机器学习的课件，面向大学生，时长45分钟"
}
```

**curl 示例**:

```bash
curl -X POST http://localhost:8000/api/asr \
  -F "file=@/path/to/recording.wav"
```

**JavaScript fetch 示例（使用 MediaRecorder）**:

```javascript
// 录音
let mediaRecorder;
let audioChunks = [];

navigator.mediaDevices.getUserMedia({ audio: true })
  .then(stream => {
    mediaRecorder = new MediaRecorder(stream);
    
    mediaRecorder.ondataavailable = (event) => {
      audioChunks.push(event.data);
    };
    
    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
      
      // 上传识别
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.webm');
      
      const response = await fetch('http://localhost:8000/api/asr', {
        method: 'POST',
        body: formData
      });
      
      const result = await response.json();
      console.log('识别结果:', result.text);
    };
    
    mediaRecorder.start();
  });

// 停止录音
// mediaRecorder.stop();
```

**环境要求**:

需要配置 `DASHSCOPE_API_KEY` 环境变量。

**支持的音频格式**:

- WAV (推荐)
- MP3
- WebM (浏览器录音常用格式)

**识别特性**:

- 支持中英文混合识别
- 短音频（<60s）使用实时识别
- 长音频自动切换异步转写

---

## 监控 API

### 1. 健康检查

检查系统健康状态和资源使用情况。

**接口**: `GET /health`

**响应示例**:

```json
{
  "status": "healthy",
  "timestamp": "2026-04-21T10:30:00.000Z",
  "system": {
    "memory": {
      "total_mb": 16384,
      "used_mb": 8192,
      "available_mb": 8192,
      "percent": 50.0
    },
    "cpu": {
      "percent": 25.5,
      "count": 8
    },
    "disk": {
      "percent": 45.2
    }
  },
  "errors": {
    "total_errors": 5,
    "error_counts": {
      "POST /api/generate:ValueError": 3,
      "POST /api/chat:HTTPException": 2
    },
    "endpoints_with_errors": 2
  },
  "uptime_seconds": 3600.5
}
```

**状态说明**:

- `healthy`: 系统正常运行
- `degraded`: 系统资源紧张（内存或 CPU >90%）
- `unhealthy`: 系统异常（错误数 >100 或健康检查失败）

**curl 示例**:

```bash
curl -X GET http://localhost:8000/health
```

**JavaScript fetch 示例**:

```javascript
const response = await fetch('http://localhost:8000/health');
const health = await response.json();

if (health.status === 'healthy') {
  console.log('System is healthy');
} else {
  console.warn('System status:', health.status);
}
```

---

### 2. Prometheus 指标

导出 Prometheus 格式的监控指标。

**接口**: `GET /metrics`

**响应格式**: `text/plain` (Prometheus 格式)

**响应示例**:

```
# HELP fastppt_requests_total Total request count
# TYPE fastppt_requests_total counter
fastppt_requests_total{method="POST",endpoint="/api/chat",status="200"} 150

# HELP fastppt_request_duration_seconds Request duration in seconds
# TYPE fastppt_request_duration_seconds histogram
fastppt_request_duration_seconds_bucket{method="POST",endpoint="/api/generate",le="0.5"} 10
fastppt_request_duration_seconds_bucket{method="POST",endpoint="/api/generate",le="1.0"} 25

# HELP fastppt_ppt_generated_total Total PPTs generated
# TYPE fastppt_ppt_generated_total counter
fastppt_ppt_generated_total 42

# HELP fastppt_memory_usage_bytes Memory usage in bytes
# TYPE fastppt_memory_usage_bytes gauge
fastppt_memory_usage_bytes 8589934592
```

**curl 示例**:

```bash
curl -X GET http://localhost:8000/metrics
```

---

### 3. 错误日志

获取最近的错误日志（管理员接口）。

**接口**: `GET /admin/errors`

**请求参数**:

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| endpoint | string | 否 | null | 过滤特定接口的错误 |
| limit | integer | 否 | 50 | 返回错误数量 |

**响应示例**:

```json
{
  "errors": [
    {
      "timestamp": "2026-04-21T10:25:30.000Z",
      "endpoint": "POST /api/generate",
      "error_type": "ValueError",
      "message": "Invalid intent format",
      "stack_trace": "Traceback (most recent call last):\n  File..."
    }
  ],
  "summary": {
    "total_errors": 5,
    "error_counts": {
      "POST /api/generate:ValueError": 3,
      "POST /api/chat:HTTPException": 2
    },
    "endpoints_with_errors": 2
  }
}
```

**curl 示例**:

```bash
# 获取所有错误
curl -X GET "http://localhost:8000/admin/errors?limit=50"

# 获取特定接口的错误
curl -X GET "http://localhost:8000/admin/errors?endpoint=POST%20/api/generate&limit=20"
```

**JavaScript fetch 示例**:

```javascript
const response = await fetch('http://localhost:8000/admin/errors?limit=50');
const result = await response.json();

console.log('Total errors:', result.summary.total_errors);
result.errors.forEach(error => {
  console.error(`[${error.timestamp}] ${error.endpoint}: ${error.message}`);
});
```

---

### 4. 性能统计

获取接口性能统计数据（管理员接口）。

**接口**: `GET /admin/performance`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| endpoint | string | 否 | 过滤特定接口的统计 |

**响应示例（单个接口）**:

```json
{
  "endpoint": "POST /api/generate",
  "count": 150,
  "avg_duration": 12.5,
  "min_duration": 8.2,
  "max_duration": 25.3,
  "p50": 11.8,
  "p95": 20.1,
  "p99": 23.7
}
```

**响应示例（所有接口）**:

```json
{
  "POST /api/chat": {
    "endpoint": "POST /api/chat",
    "count": 300,
    "avg_duration": 2.3,
    "min_duration": 0.5,
    "max_duration": 8.1,
    "p50": 2.0,
    "p95": 5.2,
    "p99": 7.5
  },
  "POST /api/generate": {
    "endpoint": "POST /api/generate",
    "count": 150,
    "avg_duration": 12.5,
    "min_duration": 8.2,
    "max_duration": 25.3,
    "p50": 11.8,
    "p95": 20.1,
    "p99": 23.7
  }
}
```

**curl 示例**:

```bash
# 获取所有接口统计
curl -X GET http://localhost:8000/admin/performance

# 获取特定接口统计
curl -X GET "http://localhost:8000/admin/performance?endpoint=POST%20/api/generate"
```

**JavaScript fetch 示例**:

```javascript
const response = await fetch('http://localhost:8000/admin/performance');
const stats = await response.json();

Object.entries(stats).forEach(([endpoint, data]) => {
  console.log(`${endpoint}:`);
  console.log(`  Average: ${data.avg_duration}s`);
  console.log(`  P95: ${data.p95}s`);
  console.log(`  Count: ${data.count}`);
});
```

---

## 错误码说明

### HTTP 状态码

| 状态码 | 说明 | 常见原因 |
|--------|------|----------|
| 200 | 成功 | 请求正常处理 |
| 400 | 请求错误 | 参数缺失、格式错误、文件类型不支持 |
| 404 | 资源不存在 | 文件不存在、job_id 无效 |
| 500 | 服务器错误 | LLM 调用失败、文件解析失败、生成失败 |
| 503 | 服务不可用 | 配置缺失（API Key 等） |

### 错误响应格式

所有错误响应遵循统一格式：

```json
{
  "detail": "错误描述信息"
}
```

### 常见错误示例

**1. 配置缺失**

```json
{
  "detail": "RAGFlow API key not configured. Set RAGFLOW_API_KEY environment variable."
}
```

**解决方案**: 检查环境变量配置。

**2. 文件类型不支持**

```json
{
  "detail": "不支持的文件类型：.exe"
}
```

**解决方案**: 使用支持的文件格式（PDF, DOCX, TXT, JPG, MP4 等）。

**3. 文件不存在**

```json
{
  "detail": "文件不存在"
}
```

**解决方案**: 检查文件名是否正确，确保文件已生成。

**4. LLM 调用失败**

```json
{
  "detail": "LLM 调用失败: API rate limit exceeded"
}
```

**解决方案**: 检查 API 配额，稍后重试。

**5. 生成失败**

```json
{
  "detail": "课件内容生成失败: Invalid intent format"
}
```

**解决方案**: 检查 intent 参数格式是否正确。

**6. Job 不存在**

```json
{
  "detail": "job 不存在"
}
```

**解决方案**: 确保 job_id 正确，任务未超时。

---

## 错误处理最佳实践

### JavaScript 统一错误处理

```javascript
async function apiCall(url, options = {}) {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API call failed:', error.message);
    
    // 根据错误类型处理
    if (error.message.includes('API key')) {
      alert('系统配置错误，请联系管理员');
    } else if (error.message.includes('rate limit')) {
      alert('请求过于频繁，请稍后重试');
    } else {
      alert(`操作失败: ${error.message}`);
    }
    
    throw error;
  }
}

// 使用示例
try {
  const result = await apiCall('http://localhost:8000/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages: [...] })
  });
  console.log('Success:', result);
} catch (error) {
  // 错误已在 apiCall 中处理
}
```

---

## 完整使用流程示例

### 场景：用户对话生成课件

```javascript
// 1. 用户发送消息
const chatResponse = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    messages: [
      { role: 'user', content: '我想制作一个关于Python的课件，面向初学者，45分钟' }
    ],
    stream: false,
    use_agent: false
  })
});

const chatResult = await chatResponse.json();

// 2. 检查是否准备好生成
if (chatResult.intent_ready) {
  console.log('Intent ready:', chatResult.intent);
  
  // 3. 启动生成任务
  const startResponse = await fetch('http://localhost:8000/api/generate/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      intent: chatResult.intent
    })
  });
  
  const { job_id } = await startResponse.json();
  console.log('Job started:', job_id);
  
  // 4. 监听生成进度
  const eventSource = new EventSource(`http://localhost:8000/api/generate/${job_id}/stream`);
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    // 更新进度条
    updateProgressBar(data.progress, data.message);
    
    if (data.done) {
      if (data.error) {
        alert('生成失败: ' + data.error);
      } else {
        console.log('Generation complete!');
        
        // 5. 下载生成的文件
        downloadFile(data.docx);
        
        // 6. 显示预览
        showPreview(data.slides_json);
      }
      
      eventSource.close();
    }
  };
}

// 辅助函数
function updateProgressBar(progress, message) {
  document.getElementById('progress-bar').style.width = progress + '%';
  document.getElementById('progress-text').textContent = message;
}

function downloadFile(filename) {
  const a = document.createElement('a');
  a.href = `http://localhost:8000/api/download/${filename}`;
  a.download = filename;
  a.click();
}

function showPreview(slidesJson) {
  // 渲染课件预览
  console.log('Slides:', slidesJson.pages.length);
}
```

---

## 环境变量配置

运行 FastPPT 需要配置以下环境变量：

```bash
# DeepSeek API（必需）
DEEPSEEK_API_KEY=your_deepseek_api_key

# RAGFlow 配置（可选，用于检索 API）
RAGFLOW_BASE_URL=http://localhost:9380
RAGFLOW_API_KEY=your_ragflow_api_key
RAGFLOW_KB_ID=your_knowledge_base_id

# DashScope API（可选，用于语音识别）
DASHSCOPE_API_KEY=your_dashscope_api_key

# 日志配置
LOG_LEVEL=INFO
APP_ENV=development

# CORS 配置
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## 附录

### API 响应头

所有响应包含以下标准头：

- `X-Response-Time`: 请求处理时间（秒）
- `Content-Type`: 响应内容类型
- `Cache-Control`: 缓存控制（SSE 流为 `no-cache`）

### 速率限制

当前版本无速率限制，但建议：

- 对话 API: 每秒不超过 10 次请求
- 生成 API: 每分钟不超过 5 次请求
- 上传 API: 每分钟不超过 20 次请求

### 超时设置

- 对话 API: 30 秒
- 生成 API: 120 秒（SSE 流）
- 上传 API: 60 秒
- 下载 API: 无超时

---

**文档版本**: 1.0.0  
**最后更新**: 2026-04-21  
**维护者**: FastPPT Team
