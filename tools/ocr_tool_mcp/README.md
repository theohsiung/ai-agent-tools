# OCR Tool MCP Server

MCP (Model Context Protocol) server for OCR functionality using Chandra model.

## Installation

```bash
cd tools/ocr_tool_mcp
uv sync
```

## Usage

### Run as standalone server

```bash
uv run python mcp_server.py
```

### Configure in Claude Code

Add to your Claude Code MCP settings (`~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ocr-tool": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/tools/ocr_tool_mcp", "python", "mcp_server.py"]
    }
  }
}
```

## Available Tools

### `ocr`

Perform OCR on an image and return structured text.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image_base64` | string | Yes | Base64 encoded image data |
| `prompt_type` | string | No | `ocr_layout` (default) or `ocr` |
| `custom_prompt` | string | No | Custom prompt to override default |

**Prompt Types:**

- `ocr_layout`: Returns text with bounding box layout information
- `ocr`: Returns plain text only

## Requirements

- CUDA-enabled GPU (for model inference)
- Python 3.10+
