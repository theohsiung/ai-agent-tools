# --- Import all necessary libraries for our entire adventure ---
import os
import re
import asyncio
from dotenv import load_dotenv
from IPython.display import display, Markdown
import google.generativeai as genai
from google.adk.agents import Agent, SequentialAgent, LoopAgent, ParallelAgent, LlmAgent
from google.adk.tools import google_search, ToolContext
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService, Session
from google.genai.types import Content, Part
from getpass import getpass
from utils.run_agent_query import run_agent_query

load_dotenv()
print("✅ All libraries are ready to go!")

# vLLM configuration
VLLM_API_BASE = os.environ.get("VLLM_API_BASE", "http://0.0.0.0:8000/v1")
VLLM_MODEL = "Qwen/Qwen3-4B-Instruct-2507"

session_service = InMemorySessionService()
my_user_id = "user_12345"

# Use vLLM as OpenAI-compatible endpoint
base_model = LiteLlm(
    model=f"openai/{VLLM_MODEL}",
    api_base=VLLM_API_BASE,
    api_key="EMPTY",  # vLLM doesn't require API key
    timeout=120
)

# Agent 1: Proposes an initial plan
planner_agent = LlmAgent(
    name="planner_agent", model=base_model, tools=[],
    instruction="You are a trip planner. Based on the user's request, propose a single activity and a single restaurant. Output only the names, like: 'Activity: Exploratorium, Restaurant: La Mar'.",
    output_key="current_plan"
)

print("🤖 Agent team updated with an iterative LoopAgent workflow!")

async def run_day_trip_genie():
    # Create a new, single-use session for this query
    day_trip_session = await session_service.create_session(
        app_name=planner_agent.name,
        user_id=my_user_id
    )

    # Note the new budget constraint in the query!
    query = "Plan a relaxing and artsy day trip near Sunnyvale, CA. Keep it affordable!"
    print(f"🗣️ User Query: '{query}'")

    await run_agent_query(planner_agent, query, day_trip_session, my_user_id, session_service)

asyncio.run(run_day_trip_genie())
