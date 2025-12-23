# --- Import all necessary libraries ---
import os
import sys
import base64
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
VLLM_API_BASE = os.environ.get("VLLM_API_BASE", "http://0.0.0.0:8000/v1")
VLLM_MODEL = "Qwen/Qwen3-4B-Instruct-2507"

OCR_MCP_PATH = os.path.join(os.path.dirname(__file__), "..", "tools", "ocr_tool_mcp")


def load_image_as_base64(image_path: str) -> str:
    """Load an image file and convert to base64 string."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    with open(path, "rb") as f:
        image_data = f.read()

    return base64.b64encode(image_data).decode("utf-8")

session_service = InMemorySessionService()
my_user_id = "user_12345"

# Use vLLM as OpenAI-compatible endpoint
base_model = LiteLlm(
    model=f"openai/{VLLM_MODEL}",
    api_base=VLLM_API_BASE,
    api_key="EMPTY",  # vLLM doesn't require API key
    timeout=120
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
    # Get OCR tools from MCP server
    ocr_toolset = await create_mcp_toolset()
    tools = await ocr_toolset.get_tools()
    print(f"📦 Loaded {len(tools)} tools from OCR MCP server")

    # Create agent with OCR tools
    ocr_agent = LlmAgent(
        name="ocr_agent",
        model=base_model,
        tools=tools,
        instruction="""你是一為OCR助手。當用戶提供一張圖片（以base64編碼）時，
                    使用'ocr'工具從中提取文字與HTML格式。""",
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

    # Load image as base64
    print(f"📷 Loading image: {image_path}")
    image_base64 = load_image_as_base64(image_path)
    print(f"✅ Image loaded ({len(image_base64)} chars)")

    # Create agent with MCP tools
    ocr_md_gen_agent, ocr_toolset = await create_agents()

    try:
        # Create session
        session = await session_service.create_session(
            app_name=ocr_md_gen_agent.name,
            user_id=my_user_id
        )

        # Create query with base64 image
        query = f"請對以下 base64 編碼的圖片進行 OCR 辨識：\n\n{image_base64}"
        print(f"🗣️ Sending image to OCR agent...")

        result = await run_agent_query(ocr_md_gen_agent, query, session, my_user_id, session_service)
        return result

    finally:
        # Clean up MCP connection
        await ocr_toolset.close()
        print("🔌 MCP connection closed")


def main():
    image_path = "/home/theo/projects/ai-agent-tools/asset/example_slide.png"
    result = asyncio.run(run_ocr(image_path))
    print("\n📝 Final OCR Markdown Output:\n")
    print(result)



if __name__ == "__main__":
    main()
