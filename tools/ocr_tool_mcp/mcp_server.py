import os
os.environ["CUDA_VISIBLE_DEVICES"] = "2"

import sys
from mcp.server import Server
from mcp.server.sse import SseServerTransport
import uvicorn


# Global model instance
model = None


def load_model():
    global model
    if model is None:
        from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
        
        print("Loading OCR model...", file=sys.stderr)
        model = Qwen3VLForConditionalGeneration.from_pretrained("datalab-to/chandra").cuda()
        model.processor = AutoProcessor.from_pretrained("datalab-to/chandra")
        print("Model loaded!", file=sys.stderr)
    return model


def perform_ocr(image_path: str, prompt_type: str = "ocr_layout", custom_prompt: str | None = None) -> dict:
    """Perform OCR on an image."""
    from PIL import Image
    from chandra.model.hf import generate_hf
    from chandra.model.schema import BatchInputItem
    from chandra.output import parse_markdown
    
    load_model()

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
async def list_tools():
    from mcp.types import Tool
    return [
        Tool(
            name="ocr",
            description="Perform OCR on an image file",
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
                        "default": "ocr_layout"
                    }
                },
                "required": ["image_path"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    from mcp.types import TextContent
    
    if name != "ocr":
        raise ValueError(f"Unknown tool: {name}")

    try:
        print(f"Performing OCR on: {arguments.get('image_path')}", file=sys.stderr)
        result = perform_ocr(
            image_path=arguments["image_path"],
            prompt_type=arguments.get("prompt_type", "ocr_layout"),
            custom_prompt=arguments.get("custom_prompt")
        )
        print("OCR completed!", file=sys.stderr)

        response_text = f"""## OCR Result

**Markdown Output:**
{result['markdown']}

**Token Count:** {result['token_count']}
**Error:** {result['error']}
"""
        return [TextContent(type="text", text=response_text)]

    except Exception as e:
        import traceback
        print(traceback.format_exc(), file=sys.stderr)
        return [TextContent(type="text", text=f"OCR Error: {str(e)}")]


# SSE transport - 使用 ASGI 方式
sse = SseServerTransport("/messages/")


async def handle_sse(scope, receive, send):
    """Handle SSE connection as raw ASGI."""
    async with sse.connect_sse(scope, receive, send) as streams:
        await server.run(
            streams[0], streams[1], server.create_initialization_options()
        )


async def handle_messages(scope, receive, send):
    """Handle POST messages as raw ASGI."""
    await sse.handle_post_message(scope, receive, send)


async def app(scope, receive, send):
    """Main ASGI application."""
    if scope["type"] == "http":
        path = scope["path"]
        method = scope["method"]
        
        if path == "/sse" and method == "GET":
            await handle_sse(scope, receive, send)
        elif path.startswith("/messages/") and method == "POST":
            await handle_messages(scope, receive, send)
        else:
            # 404 response
            await send({
                "type": "http.response.start",
                "status": 404,
                "headers": [[b"content-type", b"text/plain"]],
            })
            await send({
                "type": "http.response.body",
                "body": b"Not Found",
            })
    elif scope["type"] == "lifespan":
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return


if __name__ == "__main__":
    print("🚀 Starting OCR MCP Server...")
    print("⏳ Pre-loading model...")
    load_model()
    print("✅ Model ready!")
    print("🌐 Server running on http://localhost:8888")
    
    uvicorn.run(app, host="0.0.0.0", port=8888)