import logging
import uvicorn
from typing import Optional
from google.adk.agents.base_agent import BaseAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a

def serve_agent(
    agent: BaseAgent,
    host: str = "0.0.0.0",
    port: int = 8000,
    protocol: str = "http",
    agent_card: Optional[str] = None
):
    """
    Universally wrap any ADK agent as an A2A server using Starlette and Uvicorn.
    
    Args:
        agent: The BaseAgent instance to serve.
        host: Host interface to bind to.
        port: Port to listen on.
        protocol: Protocol (http/https).
        agent_card: Optional path to a custom agent card JSON file.
    """
    logging.info(f"🚀 Wrapping agent '{agent.name}' as A2A server on {protocol}://{host}:{port}")
    
    # Use the official ADK to_a2a utility
    app = to_a2a(
        agent=agent,
        host=host,
        port=port,
        protocol=protocol,
        agent_card=agent_card
    )
    
    # Start the Uvicorn server
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    
    # Since this is usually called in an async context or at the end of a script
    return server
