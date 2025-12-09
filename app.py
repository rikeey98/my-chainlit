import os
from typing import Optional, List, Dict, Any
import chainlit as cl
from openai import AsyncOpenAI
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# OpenAI Compatible API Configuration
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "not-needed"),
    base_url=os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
)

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
MCP_SERVER_ENABLED = os.getenv("MCP_SERVER_ENABLED", "false").lower() == "true"


class MCPClient:
    """MCP (Model Context Protocol) Server Client"""

    def __init__(self, server_url: Optional[str] = None):
        self.server_url = server_url or os.getenv("MCP_SERVER_URL")
        self.enabled = MCP_SERVER_ENABLED and self.server_url is not None

    async def get_context(self, query: str) -> Optional[str]:
        """Fetch context from MCP server"""
        if not self.enabled:
            return None

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.server_url}/context",
                    json={"query": query}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("context")
        except Exception as e:
            print(f"MCP Server Error: {e}")

        return None

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available MCP tools"""
        if not self.enabled:
            return []

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.server_url}/tools") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("tools", [])
        except Exception as e:
            print(f"MCP Server Error: {e}")

        return []


# Initialize MCP Client
mcp_client = MCPClient()


@cl.on_chat_start
async def start():
    """Called when a new chat session starts"""

    # Initialize conversation history
    cl.user_session.set("message_history", [])

    # Welcome message
    welcome_msg = "안녕하세요! 👋\n\n"
    welcome_msg += f"**모델**: {MODEL_NAME}\n"
    welcome_msg += f"**API Base**: {os.getenv('OPENAI_API_BASE')}\n"

    if mcp_client.enabled:
        welcome_msg += f"**MCP Server**: ✅ Enabled ({mcp_client.server_url})\n"
        tools = await mcp_client.list_tools()
        if tools:
            welcome_msg += f"**Available Tools**: {', '.join([t['name'] for t in tools])}\n"
    else:
        welcome_msg += "**MCP Server**: ❌ Disabled\n"

    welcome_msg += "\n무엇을 도와드릴까요?"

    await cl.Message(content=welcome_msg).send()


@cl.on_message
async def main(message: cl.Message):
    """Called when a user sends a message"""

    # Get message history
    message_history = cl.user_session.get("message_history", [])

    # Add user message to history
    user_message = {"role": "user", "content": message.content}
    message_history.append(user_message)

    # Check if MCP context is needed
    mcp_context = None
    if mcp_client.enabled:
        mcp_context = await mcp_client.get_context(message.content)
        if mcp_context:
            # Add MCP context to the user message
            enhanced_content = f"[Context from MCP]: {mcp_context}\n\n[User Query]: {message.content}"
            user_message["content"] = enhanced_content

    # Create a message placeholder for streaming
    msg = cl.Message(content="")
    await msg.send()

    try:
        # Stream response from OpenAI compatible API
        stream = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=message_history,
            stream=True,
            temperature=0.7,
            max_tokens=2000
        )

        full_response = ""
        async for part in stream:
            if part.choices[0].delta.content:
                token = part.choices[0].delta.content
                full_response += token
                await msg.stream_token(token)

        # Update message with complete response
        await msg.update()

        # Add assistant response to history
        assistant_message = {"role": "assistant", "content": full_response}
        message_history.append(assistant_message)

        # Update session with new history
        cl.user_session.set("message_history", message_history)

    except Exception as e:
        error_msg = f"❌ Error: {str(e)}\n\n"
        error_msg += "API 연결을 확인해주세요:\n"
        error_msg += f"- API Base: {os.getenv('OPENAI_API_BASE')}\n"
        error_msg += f"- Model: {MODEL_NAME}"

        await msg.update()
        await cl.Message(content=error_msg).send()


@cl.on_settings_update
async def setup_agent(settings):
    """Called when user updates settings"""
    print(f"Settings updated: {settings}")


if __name__ == "__main__":
    # This is for development only
    # Run with: chainlit run app.py
    pass
