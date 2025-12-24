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

| Tool | Port | Endpoint | Status |
|------|------|----------|--------|
| ocr_tool_mcp | 8888 | http://localhost:8888 | Ready (via SSE) |
| ocr_agent | 8000 | http://localhost:8000 | Ready (A2A Server) |
| tts_tool | 8002 | http://localhost:8002 | TODO |

## Adding New Tools/Agents

Edit `TOOL_REGISTRY` in `main.py`:

```python
TOOL_REGISTRY = {
    "ocr_tool_mcp": "http://localhost:8888",
    "ocr_agent": "http://localhost:8000",
}
```
