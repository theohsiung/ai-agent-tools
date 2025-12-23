# --- Import all necessary libraries ---
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StdioServerParameters
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from utils.run_agent_query import run_agent_query

load_dotenv()
print("✅ All libraries are ready to go!")

# vLLM configuration
VLLM_API_BASE = os.environ.get("VLLM_API_BASE", "http://localhost:8000/v1")
VLLM_MODEL = "openai/gpt-oss-20b"

OCR_MCP_PATH = os.path.join(os.path.dirname(__file__), "..", "tools", "ocr_tool_mcp")

session_service = InMemorySessionService()
my_user_id = "user_12345"

# Use vLLM as OpenAI-compatible endpoint
base_model = LiteLlm(
    model=f"openai/{VLLM_MODEL}",
    api_base=VLLM_API_BASE,
    api_key="sk-1234",
    timeout=120,
    stream=True,
)


async def create_mcp_toolset():
    """Create MCP toolset for OCR."""
    ocr_toolset = McpToolset(
        connection_params=StdioServerParameters(
            command="uv",
            args=["run", "--directory", OCR_MCP_PATH, "python", "mcp_server.py"],
        )
    )
    return ocr_toolset


async def create_agents():
    """Create agents with MCP tools. Returns (agent, toolset) tuple."""
    ocr_toolset = await create_mcp_toolset()
    tools = await ocr_toolset.get_tools()
    print(f"📦 Loaded {len(tools)} tools from OCR MCP server")

    # Create agent with OCR tools
    ocr_agent = LlmAgent(
        name="ocr_agent",
        model=base_model,
        tools=tools,
        instruction="""你是一個 OCR 助手。當用戶提供圖片路徑時：
        1. 使用 ocr tool，將 image_path 作為參數傳入
        2. 回傳 OCR 結果
        """,
        output_key="ocr_result"
    )

    refine_agent = LlmAgent(
        name="refine_agent",
        model=base_model,
        tools=[],
        instruction="""你是一位markdown生成高手。根據OCR結果 {ocr_result} 使用markdown進行重建，
                    保留文件結構，如表格、標題等等。""",
    )

    ocr_md_gen_agent = SequentialAgent(
        name="ocr_md_gen_agent",
        sub_agents=[ocr_agent, refine_agent],
        description="An agent that performs OCR and then refines the output into markdown format."
    )
    return ocr_md_gen_agent, ocr_toolset


async def run_ocr(image_path: str):
    """Run OCR on an image file."""
    print("🚀 Starting OCR Agent...")

    # 確認圖片存在
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # 轉換成絕對路徑
    absolute_path = str(path.resolve())
    print(f"📷 Image path: {absolute_path}")

    # Create agent with MCP tools
    ocr_md_gen_agent, ocr_toolset = await create_agents()

    try:
        # Create session
        session = await session_service.create_session(
            app_name=ocr_md_gen_agent.name,
            user_id=my_user_id
        )

        # ✅ 只傳檔案路徑，非常短
        query = f"請使用 ocr tool 對這個圖片進行 OCR 辨識，圖片路徑是：{absolute_path}"
        print(f"🗣️ Sending OCR request to agent...")

        result = await run_agent_query(ocr_md_gen_agent, query, session, my_user_id, session_service)
        return result

    finally:
        await ocr_toolset.close()
        print("🔌 MCP connection closed")


def main():
    image_path = "/home/os-theo.hsiung/projects/ai-agent-tools/asset/example_slide.png"
    result = asyncio.run(run_ocr(image_path))
    print("\n📝 Final OCR Markdown Output:\n")
    print(result)


if __name__ == "__main__":
    main()