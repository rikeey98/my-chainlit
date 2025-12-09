"""
Example MCP (Model Context Protocol) Server Implementation
This is a simple example server that demonstrates how to create an MCP server
that can be integrated with the Chainlit chat application.

Run with: python mcp_server_example.py
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn

app = FastAPI(title="MCP Server Example", version="1.0.0")


class ContextRequest(BaseModel):
    query: str


class ContextResponse(BaseModel):
    context: str
    sources: Optional[List[str]] = None


class Tool(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]


class ToolCallRequest(BaseModel):
    arguments: Dict[str, Any]


class ToolCallResponse(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None


# Mock knowledge base for context retrieval
KNOWLEDGE_BASE = {
    "python": "Python is a high-level, interpreted programming language known for its simplicity and readability.",
    "fastapi": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints.",
    "chainlit": "Chainlit is a Python framework for building conversational AI applications with a focus on LLM integration.",
    "mcp": "Model Context Protocol (MCP) is a protocol for providing context and tools to language models.",
}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "MCP Server"}


@app.post("/context", response_model=ContextResponse)
async def get_context(request: ContextRequest):
    """
    Retrieve relevant context based on the query
    This is a simple keyword-based search for demonstration
    """
    query_lower = request.query.lower()

    # Search for relevant context
    relevant_contexts = []
    sources = []

    for key, value in KNOWLEDGE_BASE.items():
        if key in query_lower:
            relevant_contexts.append(f"{key.upper()}: {value}")
            sources.append(f"knowledge_base:{key}")

    if relevant_contexts:
        context = "\n\n".join(relevant_contexts)
    else:
        context = "No specific context found for this query."

    return ContextResponse(context=context, sources=sources)


@app.get("/tools", response_model=Dict[str, List[Tool]])
async def list_tools():
    """List available tools"""
    tools = [
        Tool(
            name="web_search",
            description="Search the web for information",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="calculate",
            description="Perform mathematical calculations",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
        ),
        Tool(
            name="get_weather",
            description="Get weather information for a location",
            parameters={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or coordinates"
                    },
                    "units": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "default": "celsius"
                    }
                },
                "required": ["location"]
            }
        )
    ]

    return {"tools": [tool.dict() for tool in tools]}


@app.post("/tools/{tool_name}/call", response_model=ToolCallResponse)
async def call_tool(tool_name: str, request: ToolCallRequest):
    """Execute a tool"""

    if tool_name == "calculate":
        try:
            expression = request.arguments.get("expression")
            if not expression:
                raise ValueError("Expression is required")

            # Safe evaluation (in production, use a proper math parser)
            result = eval(expression, {"__builtins__": {}})
            return ToolCallResponse(success=True, result=str(result))

        except Exception as e:
            return ToolCallResponse(success=False, error=str(e))

    elif tool_name == "web_search":
        query = request.arguments.get("query")
        num_results = request.arguments.get("num_results", 5)

        # Mock search results
        return ToolCallResponse(
            success=True,
            result={
                "query": query,
                "results": [
                    f"Mock search result {i+1} for: {query}"
                    for i in range(num_results)
                ]
            }
        )

    elif tool_name == "get_weather":
        location = request.arguments.get("location")
        units = request.arguments.get("units", "celsius")

        # Mock weather data
        return ToolCallResponse(
            success=True,
            result={
                "location": location,
                "temperature": 22 if units == "celsius" else 72,
                "units": units,
                "conditions": "Partly cloudy",
                "humidity": 65
            }
        )

    else:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")


if __name__ == "__main__":
    print("🚀 Starting MCP Server on http://localhost:3000")
    print("📚 Available endpoints:")
    print("  - GET  /health")
    print("  - POST /context")
    print("  - GET  /tools")
    print("  - POST /tools/{tool_name}/call")
    print("\nPress CTRL+C to stop")

    uvicorn.run(app, host="0.0.0.0", port=3000, log_level="info")
