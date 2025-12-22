"""
Chainlit MCP Agent - FastMCP SSE 통합
파일 읽기 MCP 도구를 사용하는 간소화된 에이전트
"""

import os
import json
from typing import Dict, Any
import chainlit as cl
from openai import AsyncOpenAI
from dotenv import load_dotenv
from mcp_client import MCPClient

# 환경 변수 로드
load_dotenv(".env.mcp")

# OpenAI 클라이언트 초기화
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "not-needed"),
    base_url=os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
)

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8100")

# MCP 클라이언트 초기화
mcp = None


async def get_mcp_tools() -> list:
    """MCP 서버에서 도구 목록 가져오기"""
    global mcp
    if mcp is None:
        mcp = MCPClient(MCP_SERVER_URL)

    tools = await mcp.list_tools()

    # OpenAI function calling 형식으로 변환
    openai_tools = []
    for tool in tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("parameters", {
                    "type": "object",
                    "properties": {}
                })
            }
        })

    return openai_tools


async def execute_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """MCP 도구 실행"""
    global mcp
    if mcp is None:
        mcp = MCPClient(MCP_SERVER_URL)

    return await mcp.call_tool(tool_name, arguments)


@cl.on_chat_start
async def start():
    """채팅 시작 시 실행"""
    cl.user_session.set("message_history", [])

    # MCP 서버 연결 확인
    try:
        tools = await get_mcp_tools()
        tool_names = [t["function"]["name"] for t in tools]

        welcome_msg = "# 🤖 File MCP Agent\n\n"
        welcome_msg += f"**모델**: {MODEL_NAME}\n"
        welcome_msg += f"**MCP Server**: {MCP_SERVER_URL}\n\n"

        if tools:
            welcome_msg += "## 📁 사용 가능한 도구\n"
            for name in tool_names:
                welcome_msg += f"- `{name}`\n"
            welcome_msg += "\n무엇을 도와드릴까요?\n\n"
            welcome_msg += "**예시**:\n"
            welcome_msg += "- 'README.md 파일을 읽어줘'\n"
            welcome_msg += "- '현재 디렉토리의 파일 목록을 보여줘'\n"
            welcome_msg += "- '모든 Python 파일을 찾아줘'"
        else:
            welcome_msg += "⚠️ MCP 서버에 연결할 수 없습니다.\n"
            welcome_msg += f"서버가 {MCP_SERVER_URL}에서 실행 중인지 확인하세요."

        await cl.Message(content=welcome_msg).send()

    except Exception as e:
        error_msg = f"❌ MCP 서버 연결 실패: {str(e)}\n\n"
        error_msg += "다음을 확인하세요:\n"
        error_msg += "1. MCP 서버가 실행 중인지 확인\n"
        error_msg += "2. MCP_SERVER_URL 설정 확인"
        await cl.Message(content=error_msg).send()


@cl.on_message
async def main(message: cl.Message):
    """메시지 처리"""
    message_history = cl.user_session.get("message_history", [])

    # 사용자 메시지 추가
    message_history.append({
        "role": "user",
        "content": message.content
    })

    # 응답 메시지 생성
    msg = cl.Message(content="")
    await msg.send()

    try:
        # MCP 도구 가져오기
        tools = await get_mcp_tools()

        if not tools:
            await msg.stream_token("⚠️ MCP 서버에 연결할 수 없습니다.")
            await msg.update()
            return

        # LLM에게 요청 (도구 포함)
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=message_history,
            tools=tools,
            tool_choice="auto",
            temperature=0.7
        )

        assistant_message = response.choices[0].message
        tool_calls = assistant_message.tool_calls

        # 도구 호출이 있는 경우
        if tool_calls:
            # 어시스턴트 메시지 저장
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

            # 각 도구 실행
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                # 사용자에게 도구 실행 표시
                await msg.stream_token(f"\n\n🔧 **{tool_name}** 실행 중...\n")
                await msg.stream_token(f"```json\n{json.dumps(tool_args, indent=2, ensure_ascii=False)}\n```\n")

                # 도구 실행
                result = await execute_mcp_tool(tool_name, tool_args)

                # 결과 저장
                message_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps(result, ensure_ascii=False)
                })

                # 결과 표시
                if result.get("success"):
                    await msg.stream_token("✅ 성공\n")
                else:
                    await msg.stream_token(f"❌ 실패: {result.get('error', 'Unknown error')}\n")

            # 최종 응답 생성
            await msg.stream_token("\n---\n\n")

            final_response = await client.chat.completions.create(
                model=MODEL_NAME,
                messages=message_history,
                stream=True,
                temperature=0.7
            )

            full_response = ""
            async for part in final_response:
                if part.choices[0].delta.content:
                    token = part.choices[0].delta.content
                    full_response += token
                    await msg.stream_token(token)

            message_history.append({
                "role": "assistant",
                "content": full_response
            })

        else:
            # 도구 호출 없음 - 직접 응답
            if assistant_message.content:
                await msg.stream_token(assistant_message.content)
                message_history.append({
                    "role": "assistant",
                    "content": assistant_message.content
                })

        await msg.update()
        cl.user_session.set("message_history", message_history)

    except Exception as e:
        error_msg = f"\n\n❌ 오류 발생: {str(e)}\n\n"
        error_msg += "다음을 확인하세요:\n"
        error_msg += f"- LLM API: {os.getenv('OPENAI_API_BASE')}\n"
        error_msg += f"- MCP Server: {MCP_SERVER_URL}"

        await msg.stream_token(error_msg)
        await msg.update()


@cl.on_chat_end
async def end():
    """채팅 종료 시 실행"""
    global mcp
    if mcp:
        await mcp.close()


if __name__ == "__main__":
    pass
