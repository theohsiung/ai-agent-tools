# AI Agent Tools Gateway

Unified API gateway for AI Agent tools.

## Quick Start

```bash
cd gateway
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### List Tools
```bash
GET /tools
```
Returns all registered tools and their availability.

### Get Tool Spec
```bash
GET /tools/{tool_name}/spec
```
Returns the OpenAPI spec for a specific tool.

### Invoke Tool
```bash
POST /invoke
{
    "tool": "ocr_tool",
    "method": "ocr",
    "params": {
        "image_base64": "...",
        "prompt_type": "ocr_layout"
    }
}
```

### Proxy Request
```bash
POST /proxy/ocr_tool/ocr
{
    "image_base64": "...",
    "prompt_type": "ocr_layout"
}
```
Directly proxy requests to tools.

### Health Check
```bash
GET /health
```

## Tool Registry

Tools are registered in `main.py`:

| Tool | Port | Endpoint |
|------|------|----------|
| ocr_tool | 8001 | http://localhost:8001 |
| tts_tool | 8002 | http://localhost:8002 |
| embedding_tool | 8003 | http://localhost:8003 |

## Adding New Tools

Edit `TOOL_REGISTRY` in `main.py`:

```python
TOOL_REGISTRY = {
    "ocr_tool": "http://localhost:8001",
    "my_new_tool": "http://localhost:8004",
}
```
