# AI Agents

This directory contains AI Agents built using the Google Agent Development Kit (ADK).

## OCR Agent (`ocrAgent.py`)

A powerful agent that combines OCR capabilities with Markdown refinement.

### Functionality:
- **OCR Integration**: Connects to the `ocr_tool_mcp` server.
- **Sequential Workflow**:
    1. Performs OCR on a given image path.
    2. Refines the OCR text into well-structured Markdown (tables, titles, etc.).
- **Dual Operating Modes**: Standalone Script or A2A Server.

### Running the Agent:

#### 1. CLI Mode (Individual Task)
Executes a single OCR task as defined in the `main()` function.
```bash
uv run python ocrAgent/ocrAgent.py
```

#### 2. A2A Server Mode
Starts an A2A-compliant HTTP server exposing the agent's capabilities.
```bash
uv run python ocrAgent/ocrAgent.py --server
```
The server will be available at `http://0.0.0.0:8000`.

### Requirements:
- `google-adk`
- `litellm`
- Valid LLM endpoint (vLLM or OpenAI compatible)
- Running OCR MCP server (see `tools/ocr_tool_mcp`)
