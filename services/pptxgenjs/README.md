# FastPPT PptxGenJS Service

Node.js microservice for generating PowerPoint presentations using PptxGenJS library.

## Features

- **11 Slide Types**: Cover, Agenda, Content, Code, Formula, Example, Two-Column, Image, Quote, Summary, Animation
- **Chinese Font Support**: Microsoft YaHei (微软雅黑) with proper language tags
- **Fast Generation**: Optimized for ~2 seconds per slide
- **RESTful API**: Simple HTTP endpoints for integration
- **Theme Support**: Education and Business themes
- **Error Handling**: Comprehensive error handling and logging

## Installation

```bash
cd services/pptxgenjs
npm install
```

## Usage

### Start Server

```bash
# Production
npm start

# Development (with auto-reload)
npm run dev
```

Server runs on port 3000 by default (configurable via `PORT` environment variable).

### API Endpoints

#### Health Check
```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "pptxgenjs-service",
  "version": "1.0.0",
  "timestamp": "2024-01-20T10:30:00.000Z"
}
```

#### Generate PPTX
```bash
POST /generate
Content-Type: application/json
```

Request body:
```json
{
  "teaching_spec": {
    "title": "人工智能基础",
    "subject": "计算机科学",
    "teacher": "张老师"
  },
  "pages": [
    {
      "type": "cover",
      "title": "人工智能基础",
      "subtitle": "第一章：机器学习概述"
    },
    {
      "type": "content",
      "title": "什么是机器学习",
      "bullets": [
        "机器学习是人工智能的一个分支",
        "通过数据和经验自动改进算法",
        "无需显式编程即可学习模式"
      ],
      "tip": "重点理解机器学习的核心概念"
    },
    {
      "type": "code",
      "title": "Python示例",
      "language": "python",
      "code": "import numpy as np\nfrom sklearn.linear_model import LinearRegression\n\nmodel = LinearRegression()\nmodel.fit(X_train, y_train)",
      "explanation": "使用scikit-learn训练线性回归模型"
    }
  ],
  "theme": "education",
  "metadata": {
    "author": "张老师",
    "filename": "ai-basics.pptx"
  }
}
```

Response: Binary PPTX file

#### Get Supported Slide Types
```bash
GET /slide-types
```

#### Get Available Themes
```bash
GET /themes
```

## Supported Slide Types

Based on `backend/core/slide_blocks.py`:

1. **cover** - Title slide with main title, subtitle, and date
2. **agenda** - Table of contents with numbered items
3. **content** - Standard content slide with title, bullets, and optional teaching tip
4. **code** - Code block with syntax highlighting and explanation
5. **formula** - Mathematical formulas with explanation
6. **example** - Case study with problem, steps, and answer
7. **two_column** - Side-by-side comparison layout
8. **image** - Image slide with title and caption
9. **quote** - Centered quote with optional author
10. **summary** - Summary slide with key takeaways
11. **animation** - Placeholder for interactive animations

## Block Types Mapping

| Python Block Type | PptxGenJS Implementation |
|-------------------|--------------------------|
| TextBlock | `slide.addText()` |
| BulletBlock | `slide.addText()` with bullet option |
| CodeBlock | `slide.addText()` with code styling |
| FormulaBlock | `slide.addText()` with formula formatting |
| CaseBlock | Multiple `slide.addText()` calls |
| TableBlock | Two-column layout |
| ImageBlock | `slide.addImage()` |
| FlowchartBlock | Placeholder (future enhancement) |

## Themes

### Education Theme (Default)
- Primary: #4472C4 (Blue)
- Secondary: #ED7D31 (Orange)
- Accent: #70AD47 (Green)
- Font: Microsoft YaHei

### Business Theme
- Primary: #1F4E78 (Dark Blue)
- Secondary: #C55A11 (Dark Orange)
- Accent: #548235 (Dark Green)
- Font: Microsoft YaHei

## Performance

- Target: ~2 seconds per slide
- Compression enabled for smaller file sizes
- Async processing for better throughput
- Response headers include generation metrics:
  - `X-Generation-Time`: Total time in milliseconds
  - `X-Slide-Count`: Number of slides generated

## Docker Deployment

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["node", "server.js"]
```

Build and run:
```bash
docker build -t fastppt-pptxgenjs .
docker run -p 3000:3000 fastppt-pptxgenjs
```

## Integration with FastAPI

```python
import httpx

async def generate_pptx(slides_data: dict) -> bytes:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "http://localhost:3000/generate",
            json=slides_data
        )
        response.raise_for_status()
        return response.content
```

## Error Handling

The service returns appropriate HTTP status codes:

- `200 OK` - Successful generation
- `400 Bad Request` - Invalid input (missing pages, etc.)
- `500 Internal Server Error` - Generation failure

Error response format:
```json
{
  "error": "Generation failed",
  "message": "Detailed error message"
}
```

## Logging

All requests are logged with:
- HTTP method and path
- Response status code
- Duration in milliseconds

Generation logs include:
- Number of slides
- Total generation time
- Average time per slide

## Environment Variables

- `PORT` - Server port (default: 3000)
- `NODE_ENV` - Environment mode (development/production)

## Testing

```bash
# Test health endpoint
curl http://localhost:3000/health

# Test generation with sample data
curl -X POST http://localhost:3000/generate \
  -H "Content-Type: application/json" \
  -d @sample-request.json \
  --output test.pptx
```

## Troubleshooting

### Chinese characters not displaying
- Ensure `fontFace: 'Microsoft YaHei'` is set
- Add `lang: 'zh-CN'` to text options

### Images not loading
- Use Base64 encoded images for best performance
- Ensure URLs are accessible from the server
- Check image format (PNG, JPG supported)

### Large file generation timeout
- Increase client timeout settings
- Consider pagination for very large presentations
- Enable compression (already enabled by default)

## Future Enhancements

- [ ] LaTeX formula rendering
- [ ] Chart generation support
- [ ] Custom template upload
- [ ] Batch generation API
- [ ] WebSocket for progress updates
- [ ] Caching for repeated generations

## References

- [PptxGenJS Documentation](https://gitbrent.github.io/PptxGenJS/)
- [FastPPT Backend](../../backend/)
- [Slide Blocks Schema](../../backend/core/slide_blocks.py)

## License

MIT
