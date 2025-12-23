import sys
import threading
from enum import Enum

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pydantic import BaseModel, Field


class PromptType(str, Enum):
    ocr_layout = "ocr_layout"
    ocr = "ocr"


class OCRInput(BaseModel):
    image_path: str = Field(..., description="Path to image file")
    prompt_type: str = Field(default="ocr_layout", description="Prompt type: 'ocr_layout' or 'ocr'")
    custom_prompt: str | None = Field(default=None, description="Custom prompt (overrides prompt_type)")


# Global model instance
model = None
model_loading = False
model_lock = threading.Lock()


def load_model():
    global model, model_loading
    with model_lock:
        if model is None and not model_loading:
            model_loading = True
            from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
            print("Loading OCR model on GPU 5...", file=sys.stderr)
            # ✅ 改成 cuda(5)，使用空閒的 GPU 5
            model = Qwen3VLForConditionalGeneration.from_pretrained("datalab-to/chandra").cuda(5)
            model.processor = AutoProcessor.from_pretrained("datalab-to/chandra")
            print("Model loaded on GPU 5!", file=sys.stderr)
    return model


def start_background_loading():
    """Start loading model in background thread."""
    thread = threading.Thread(target=load_model, daemon=True)
    thread.start()


def wait_for_model(timeout=60):
    """Wait for model to be loaded."""
    import time
    start = time.time()
    while model is None:
        if time.time() - start > timeout:
            raise TimeoutError("Model loading timed out")
        time.sleep(0.5)
    return model


def perform_ocr(image_path: str, prompt_type: str = "ocr_layout", custom_prompt: str | None = None) -> dict:
    """Perform OCR on an image."""
    from PIL import Image
    from chandra.model.hf import generate_hf
    from chandra.model.schema import BatchInputItem
    from chandra.output import parse_markdown
    
    # 等待模型載入完成
    wait_for_model(timeout=120)

    image = Image.open(image_path).convert("RGB")

    batch = [
        BatchInputItem(
            image=image,
            prompt=custom_prompt,
            prompt_type=prompt_type if not custom_prompt else None,
        )
    ]

    result = generate_hf(batch, model)[0]
    markdown = parse_markdown(result.raw)

    return {
        "raw": result.raw,
        "markdown": markdown,
        "token_count": result.token_count,
        "error": result.error,
    }


# Create MCP server
server = Server("ocr-tool-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available OCR tools."""
    return [
        Tool(
            name="ocr",
            description="Perform OCR on an image file and return structured text with layout information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_path": {
                        "type": "string",
                        "description": "Path to the image file"
                    },
                    "prompt_type": {
                        "type": "string",
                        "enum": ["ocr_layout", "ocr"],
                        "default": "ocr_layout",
                        "description": "OCR mode"
                    },
                    "custom_prompt": {
                        "type": "string",
                        "description": "Optional custom prompt"
                    }
                },
                "required": ["image_path"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name != "ocr":
        raise ValueError(f"Unknown tool: {name}")

    try:
        result = perform_ocr(
            image_path=arguments["image_path"],
            prompt_type=arguments.get("prompt_type", "ocr_layout"),
            custom_prompt=arguments.get("custom_prompt")
        )

        response_text = f"""## OCR Result

**Markdown Output:**
{result['markdown']}

**Token Count:** {result['token_count']}
**Error:** {result['error']}

<details>
<summary>Raw Output</summary>

{result['raw']}

</details>
"""
        return [TextContent(type="text", text=response_text)]

    except Exception as e:
        import traceback
        print(traceback.format_exc(), file=sys.stderr)
        return [TextContent(type="text", text=f"OCR Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    # ✅ 背景開始載入模型
    start_background_loading()
    print("Background model loading started...", file=sys.stderr)
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())