import re
import asyncio
from IPython.display import display, Markdown
import google.generativeai as genai
from google.adk.agents import Agent, SequentialAgent, LoopAgent, ParallelAgent
from google.adk.tools import google_search, ToolContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.genai.types import Content, Part
from getpass import getpass
import os
from dotenv import load_dotenv
load_dotenv()
 
import logging
#============================================================================================================================================================
# --- A Helper Function to Run Our Agents ---
# We'll use this function throughout the notebook to make running queries easy.
async def run_agent_query(agent: Agent, query: str, session: Session, user_id: str, session_service, is_router: bool = False):
    """Initializes a runner and executes a query for a given agent and session."""
    print(f"\n🚀 Running query for agent: '{agent.name}' in session: '{session.id}'...")
    # Compute the module-derived app name for diagnostics, but use `agent.name`
    # as the runner app_name so it matches sessions created with that name.
    try:
        module_app_name = agent.__class__.__module__
        module_app_name_short = module_app_name.split('.')[-1]
    except Exception:
        module_app_name_short = None
 
    logging.debug(f"agent.name='{agent.name}', module_app_name='{module_app_name_short}'")
 
    if module_app_name_short and module_app_name_short != agent.name:
        logging.debug(
            "App name mismatch diagnostic: agent.name='%s', module suggests '%s'."
            % (agent.name, module_app_name_short)
        )
 
    # Use the explicit agent.name for the runner so it can locate sessions
    runner = Runner(
        agent=agent,
        session_service=session_service,
        app_name=agent.name
    )
 
    final_response = ""
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=Content(parts=[Part(text=query)], role="user")
        ):
            if not is_router:
                # Let's see what the agent is thinking!
                print(f"EVENT: {event}")
            if event.is_final_response():
                # 遍歷所有 parts，找到非 thought 的實際回答
                # thought=True 的是思考過程，我們要跳過它
                for part in event.content.parts:
                    # 檢查是否有 thought 屬性且為 True，如果是就跳過
                    if hasattr(part, 'thought') and part.thought:
                        continue
                    # 檢查是否有 text 屬性
                    if hasattr(part, 'text') and part.text:
                        final_response = part.text
                        break
                # 如果沒找到非 thought 的回答，fallback 到第一個有 text 的 part
                if not final_response:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            final_response = part.text
                            break
    except Exception as e:
        final_response = f"An error occurred: {e}"
 
    if not is_router:
        print("\n" + "-"*50)
        print("✅ Final Response:")
        # Detect if we're running inside a Jupyter environment. If so, render Markdown;
        # otherwise print plain text so terminals show the response instead of a Markdown object.
        def _running_in_jupyter() -> bool:
            try:
                from IPython import get_ipython
                ip = get_ipython()
                if ip is None:
                    return False
                return ip.__class__.__name__ == 'ZMQInteractiveShell'
            except Exception:
                return False
 
        if _running_in_jupyter():
            display(Markdown(final_response))
        else:
            print(final_response)
        print("-"*50 + "\n")
 
    return final_response
 
# Note: session_service and my_user_id are now declared in firstAgent.py
# and passed as parameters when calling this function