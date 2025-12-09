import os
from typing import Optional, List, Dict, Any
import chainlit as cl
from openai import AsyncOpenAI
from dotenv import load_dotenv
import json
from filesystem_tools import FileSystemTools

# Load environment variables
load_dotenv()

# OpenAI Compatible API Configuration
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "not-needed"),
    base_url=os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
)

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")

# Filesystem MCP Configuration
FILESYSTEM_MCP_ENABLED = os.getenv("FILESYSTEM_MCP_ENABLED", "true").lower() == "true"
FILESYSTEM_SAFE_MODE = os.getenv("FILESYSTEM_SAFE_MODE", "true").lower() == "true"
FILESYSTEM_ALLOWED_PATHS = os.getenv("FILESYSTEM_ALLOWED_PATHS", "").split(",") if os.getenv("FILESYSTEM_ALLOWED_PATHS") else []

# Initialize Filesystem Tools
fs_tools = FileSystemTools(
    safe_mode=FILESYSTEM_SAFE_MODE,
    allowed_paths=[p.strip() for p in FILESYSTEM_ALLOWED_PATHS if p.strip()]
)


async def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """도구 실행"""
    try:
        if tool_name == "list_directory":
            return fs_tools.list_directory(**arguments)
        elif tool_name == "read_file":
            return fs_tools.read_file(**arguments)
        elif tool_name == "write_file":
            return fs_tools.write_file(**arguments)
        elif tool_name == "update_file":
            return fs_tools.update_file(**arguments)
        elif tool_name == "create_directory":
            return fs_tools.create_directory(**arguments)
        elif tool_name == "get_file_info":
            return fs_tools.get_file_info(**arguments)
        elif tool_name == "copy_item":
            return fs_tools.copy_item(**arguments)
        elif tool_name == "move_item":
            return fs_tools.move_item(**arguments)
        elif tool_name == "delete_item":
            return fs_tools.delete_item(**arguments)
        elif tool_name == "read_multiple_files":
            return fs_tools.read_multiple_files(**arguments)
        elif tool_name == "search_files":
            return fs_tools.search_files(**arguments)
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        return {"success": False, "error": f"Tool execution error: {str(e)}"}


@cl.on_chat_start
async def start():
    """Called when a new chat session starts"""

    # Initialize conversation history
    cl.user_session.set("message_history", [])

    # Welcome message
    welcome_msg = "안녕하세요! 👋\n\n"
    welcome_msg += f"**모델**: {MODEL_NAME}\n"
    welcome_msg += f"**API Base**: {os.getenv('OPENAI_API_BASE')}\n"

    if FILESYSTEM_MCP_ENABLED:
        welcome_msg += "\n**파일 시스템 MCP**: ✅ Enabled\n"
        welcome_msg += f"  - 안전 모드: {'ON' if FILESYSTEM_SAFE_MODE else 'OFF'}\n"
        if FILESYSTEM_ALLOWED_PATHS:
            welcome_msg += f"  - 허용된 경로: {', '.join(FILESYSTEM_ALLOWED_PATHS[:3])}"
            if len(FILESYSTEM_ALLOWED_PATHS) > 3:
                welcome_msg += f" 외 {len(FILESYSTEM_ALLOWED_PATHS) - 3}개"
            welcome_msg += "\n"
        else:
            welcome_msg += "  - 모든 경로 접근 가능\n"

        welcome_msg += "\n**사용 가능한 파일 시스템 기능**:\n"
        welcome_msg += "- 📁 디렉토리 조회\n"
        welcome_msg += "- 📄 파일 읽기/쓰기/수정\n"
        welcome_msg += "- 📚 여러 파일 한번에 읽기\n"
        welcome_msg += "- 🔍 파일 검색 (패턴 매칭)\n"
        welcome_msg += "- 📂 디렉토리 생성\n"
        welcome_msg += "- 📋 파일 복사/이동\n"
        welcome_msg += "- ℹ️ 파일 정보 조회\n"
    else:
        welcome_msg += "\n**파일 시스템 MCP**: ❌ Disabled\n"

    welcome_msg += "\n무엇을 도와드릴까요?"
    welcome_msg += "\n\n💡 예시:\n"
    welcome_msg += "- 'C:\\Users 디렉토리를 보여줘'\n"
    welcome_msg += "- '이 프로젝트의 모든 Python 파일을 찾아줘'\n"
    welcome_msg += "- 'app.py, config.py, utils.py 파일을 한번에 읽어줘'"

    await cl.Message(content=welcome_msg).send()


@cl.on_message
async def main(message: cl.Message):
    """Called when a user sends a message"""

    # Get message history
    message_history = cl.user_session.get("message_history", [])

    # Add user message to history
    user_message = {"role": "user", "content": message.content}
    message_history.append(user_message)

    # Create a message placeholder for streaming
    msg = cl.Message(content="")
    await msg.send()

    try:
        # Prepare tools for function calling
        tools = None
        if FILESYSTEM_MCP_ENABLED:
            tools = [
                {
                    "type": "function",
                    "function": tool_def
                }
                for tool_def in FileSystemTools.get_tool_definitions()
            ]

        # First API call with potential tool calls
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=message_history,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None,
            temperature=0.7,
            max_tokens=2000
        )

        assistant_message = response.choices[0].message
        tool_calls = assistant_message.tool_calls

        # If there are tool calls, execute them
        if tool_calls:
            # Add assistant message with tool calls to history
            message_history.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in tool_calls
                ]
            })

            # Execute each tool call
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                # Show tool execution to user
                await msg.stream_token(f"\n\n🔧 **도구 실행**: `{tool_name}`\n")
                await msg.stream_token(f"**인자**: {json.dumps(tool_args, ensure_ascii=False, indent=2)}\n\n")

                # Execute the tool
                result = await execute_tool(tool_name, tool_args)

                # Add tool result to message history
                message_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps(result, ensure_ascii=False)
                })

                # Show result to user
                if result.get("success"):
                    await msg.stream_token(f"✅ **성공**\n")
                else:
                    await msg.stream_token(f"❌ **실패**: {result.get('error', 'Unknown error')}\n")

            # Get final response with tool results
            await msg.stream_token("\n---\n\n")

            final_response = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=message_history,
                stream=True,
                temperature=0.7,
                max_tokens=2000
            )

            full_response = ""
            async for part in final_response:
                if part.choices[0].delta.content:
                    token = part.choices[0].delta.content
                    full_response += token
                    await msg.stream_token(token)

            # Add final assistant response to history
            message_history.append({
                "role": "assistant",
                "content": full_response
            })

        else:
            # No tool calls, just stream the response
            if assistant_message.content:
                await msg.stream_token(assistant_message.content)
                message_history.append({
                    "role": "assistant",
                    "content": assistant_message.content
                })
            else:
                # If there's no content, make a streaming request
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

                message_history.append({
                    "role": "assistant",
                    "content": full_response
                })

        # Update message
        await msg.update()

        # Update session with new history
        cl.user_session.set("message_history", message_history)

    except Exception as e:
        error_msg = f"❌ Error: {str(e)}\n\n"
        error_msg += "API 연결을 확인해주세요:\n"
        error_msg += f"- API Base: {os.getenv('OPENAI_API_BASE')}\n"
        error_msg += f"- Model: {MODEL_NAME}\n\n"

        # Check if model supports function calling
        if "tool" in str(e).lower() or "function" in str(e).lower():
            error_msg += "\n⚠️ 현재 모델이 Function Calling을 지원하지 않을 수 있습니다.\n"
            error_msg += ".env 파일에서 FILESYSTEM_MCP_ENABLED=false로 설정하여 비활성화할 수 있습니다."

        await msg.stream_token(error_msg)
        await msg.update()


@cl.on_settings_update
async def setup_agent(settings):
    """Called when user updates settings"""
    print(f"Settings updated: {settings}")


if __name__ == "__main__":
    # This is for development only
    # Run with: chainlit run app.py
    pass
