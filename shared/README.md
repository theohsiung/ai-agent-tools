# Shared Utilities

Common tools and helpers used across the `ai-agent-tools` project.

## A2A Wrapper (`a2a_wrapper.py`)

A universal utility to convert any Google ADK `BaseAgent` into a standard A2A (Agent-to-Agent) HTTP server.

### Key Features:
- **Universal Compatibility**: Works with `LlmAgent`, `SequentialAgent`, and any other `BaseAgent` subclasses.
- **Easy Integration**: Wrap an existing agent instance with a single function call.
- **Starlette & Uvicorn**: Built on top of modern, high-performance web standards.
- **A2A Protocol compliant**: Automatically handles Agent Card generation and RPC endpoints.

### Usage:

```python
from shared.a2a_wrapper import serve_agent
from google.adk.agents import LlmAgent

# 1. Create your agent
my_agent = LlmAgent(name="my_agent", ...)

# 2. Wrap and serve
# Returns a uvicorn.Server instance
server = serve_agent(my_agent, host="0.0.0.0", port=8000)

# 3. Start serving (usually in an async context)
await server.serve()
```
