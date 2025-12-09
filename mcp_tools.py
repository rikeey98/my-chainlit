"""
MCP (Model Context Protocol) Integration Module
Provides tools and context enhancement for the chat application
"""

import os
from typing import Optional, List, Dict, Any
import aiohttp
from dotenv import load_dotenv

load_dotenv()


class MCPServerClient:
    """
    Client for interacting with MCP servers
    Supports fetching context, tools, and executing tool calls
    """

    def __init__(self, server_url: Optional[str] = None):
        self.server_url = server_url or os.getenv("MCP_SERVER_URL")
        self.enabled = os.getenv("MCP_SERVER_ENABLED", "false").lower() == "true"
        self.timeout = aiohttp.ClientTimeout(total=10)

    async def get_context(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Fetch relevant context from MCP server based on query

        Args:
            query: User's query string

        Returns:
            Context data if available, None otherwise
        """
        if not self.enabled or not self.server_url:
            return None

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.server_url}/context",
                    json={"query": query}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"MCP Server returned status {response.status}")
        except aiohttp.ClientError as e:
            print(f"MCP Server connection error: {e}")
        except Exception as e:
            print(f"Unexpected MCP error: {e}")

        return None

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of available tools from MCP server

        Returns:
            List of tool definitions
        """
        if not self.enabled or not self.server_url:
            return []

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.server_url}/tools") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("tools", [])
        except Exception as e:
            print(f"Failed to fetch MCP tools: {e}")

        return []

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute a tool on the MCP server

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if not self.enabled or not self.server_url:
            return None

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.server_url}/tools/{tool_name}/call",
                    json={"arguments": arguments}
                ) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            print(f"Tool execution failed: {e}")

        return None

    async def health_check(self) -> bool:
        """
        Check if MCP server is healthy and reachable

        Returns:
            True if server is healthy, False otherwise
        """
        if not self.enabled or not self.server_url:
            return False

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.server_url}/health") as response:
                    return response.status == 200
        except Exception:
            return False


class LocalMCPTools:
    """
    Local MCP tools implementation for when external MCP server is not available
    Provides basic tools that can be executed locally
    """

    @staticmethod
    def get_available_tools() -> List[Dict[str, Any]]:
        """Return list of available local tools"""
        return [
            {
                "name": "calculate",
                "description": "Perform basic mathematical calculations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate"
                        }
                    },
                    "required": ["expression"]
                }
            },
            {
                "name": "search_memory",
                "description": "Search through conversation history",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]

    @staticmethod
    async def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a local tool"""
        if tool_name == "calculate":
            try:
                # Safe evaluation of mathematical expressions
                result = eval(arguments["expression"], {"__builtins__": {}})
                return {"success": True, "result": str(result)}
            except Exception as e:
                return {"success": False, "error": str(e)}

        elif tool_name == "search_memory":
            # This would search through conversation history
            return {
                "success": True,
                "result": "Memory search not yet implemented"
            }

        return {"success": False, "error": f"Unknown tool: {tool_name}"}
