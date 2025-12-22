# AI Agent Tools

A collection of local AI model APIs designed as tools for AI Agents (Google ADK / A2A protocol).

## Project Structure

```
ai-agent-tools/
├── tools/                    # A2A tool services
│   ├── ocr_tool/            # OCR service (port 8001)
│   ├── tts_tool/            # TTS service (port 8002) [TODO]
│   ├── embedding_tool/      # Embedding service (port 8003) [TODO]
│   └── ...
├── agents/                   # Google ADK agents
│   └── ...
├── gateway/                  # API gateway [TODO]
│   └── ...
└── shared/                   # Shared utilities
    └── ...
```

## Tools

| Tool | Port | Description | Status |
|------|------|-------------|--------|
| ocr_tool | 8001 | OCR with layout detection | Ready |
| tts_tool | 8002 | Text-to-Speech | TODO |
| embedding_tool | 8003 | Text embeddings | TODO |

## Quick Start

### OCR Tool

```bash
cd tools/ocr_tool

# Create virtual environment
uv sync

# Run the server
uv run uvicorn main:app --host 0.0.0.0 --port 8001

# Or run directly
uv run python main.py
```

### Test the API

```python
import base64
import requests

with open("image.png", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode()

response = requests.post("http://localhost:8001/ocr", json={
    "image_base64": image_b64,
    "prompt_type": "ocr_layout"
})
print(response.json())
```

## Tool Specification

Each tool includes a `tool_spec.json` file describing its API for A2A protocol integration.

## Adding a New Tool

1. Create a new directory under `tools/`:
   ```bash
   mkdir tools/my_tool
   cd tools/my_tool
   ```

2. Create the required files:
   - `main.py` - FastAPI application
   - `pyproject.toml` - Dependencies
   - `tool_spec.json` - A2A tool specification
   - `Dockerfile` - Container definition

3. Follow the existing `ocr_tool` as a template.

## License

MIT
