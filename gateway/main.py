import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Tool registry - maps tool names to their endpoints
TOOL_REGISTRY = {
    "ocr_tool": "http://localhost:8001",
    "tts_tool": "http://localhost:8002",
    "embedding_tool": "http://localhost:8003",
}


class ToolRequest(BaseModel):
    tool: str = Field(..., description="Tool name (e.g., 'ocr_tool')")
    method: str = Field(..., description="Method name (e.g., 'ocr')")
    params: dict = Field(default_factory=dict, description="Method parameters")


class ToolInfo(BaseModel):
    name: str
    endpoint: str
    available: bool


app = FastAPI(
    title="AI Agent Tools Gateway",
    description="Unified API gateway for AI Agent tools",
    version="1.0.0",
)


@app.get("/tools")
async def list_tools() -> list[ToolInfo]:
    """List all registered tools and their availability."""
    tools = []
    async with httpx.AsyncClient(timeout=2.0) as client:
        for name, endpoint in TOOL_REGISTRY.items():
            available = False
            try:
                resp = await client.get(f"{endpoint}/health")
                available = resp.status_code == 200
            except Exception:
                pass
            tools.append(ToolInfo(name=name, endpoint=endpoint, available=available))
    return tools


@app.get("/tools/{tool_name}/spec")
async def get_tool_spec(tool_name: str):
    """Get tool specification (tool_spec.json)."""
    if tool_name not in TOOL_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    endpoint = TOOL_REGISTRY[tool_name]
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            # Try to get openapi.json from the tool
            resp = await client.get(f"{endpoint}/openapi.json")
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Tool '{tool_name}' is not available: {e}")

    raise HTTPException(status_code=503, detail=f"Could not get spec from '{tool_name}'")


@app.post("/invoke")
async def invoke_tool(request: ToolRequest):
    """Invoke a tool method with parameters."""
    if request.tool not in TOOL_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Tool '{request.tool}' not found")

    endpoint = TOOL_REGISTRY[request.tool]
    url = f"{endpoint}/{request.method}"

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(url, json=request.params)
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Tool request timed out")
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Tool error: {e}")


@app.api_route("/proxy/{tool_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_request(tool_name: str, path: str, request: Request):
    """Proxy requests directly to tools."""
    if tool_name not in TOOL_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    endpoint = TOOL_REGISTRY[tool_name]
    url = f"{endpoint}/{path}"

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            body = await request.body()
            resp = await client.request(
                method=request.method,
                url=url,
                headers={k: v for k, v in request.headers.items() if k.lower() not in ["host", "content-length"]},
                content=body if body else None,
            )
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Tool request timed out")
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Proxy error: {e}")


@app.get("/health")
async def health():
    """Gateway health check."""
    return {"status": "ok", "tools_registered": len(TOOL_REGISTRY)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
