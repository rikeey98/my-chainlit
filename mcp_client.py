"""
MCP SSE Client
FastMCP SSE 서버와 통신하는 클라이언트
"""

import json
import httpx
from httpx_sse import connect_sse
from typing import Dict, Any, List, Optional


class MCPClient:
    """FastMCP SSE 서버와 통신하는 클라이언트"""

    def __init__(self, base_url: str = "http://localhost:8100"):
        """
        Args:
            base_url: MCP 서버 URL
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def list_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록 조회"""
        try:
            response = await self.client.get(f"{self.base_url}/tools")
            if response.status_code == 200:
                data = response.json()
                return data.get("tools", [])
            return []
        except Exception as e:
            print(f"Error fetching tools: {e}")
            return []

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        도구 호출

        Args:
            tool_name: 도구 이름
            arguments: 도구 인자

        Returns:
            도구 실행 결과
        """
        try:
            # SSE 엔드포인트로 요청
            request_data = {
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }

            async with connect_sse(
                self.client,
                "POST",
                f"{self.base_url}/sse",
                json=request_data
            ) as event_source:
                async for sse in event_source.aiter_sse():
                    # SSE 이벤트 처리
                    if sse.event == "result":
                        result = json.loads(sse.data)
                        return result
                    elif sse.event == "error":
                        error_data = json.loads(sse.data)
                        return {
                            "success": False,
                            "error": error_data.get("message", "Unknown error")
                        }

            return {
                "success": False,
                "error": "No result received from server"
            }

        except httpx.HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error calling tool: {str(e)}"
            }

    async def read_file(self, path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """파일 읽기"""
        return await self.call_tool("read_file", {"path": path, "encoding": encoding})

    async def list_directory(self, path: str) -> Dict[str, Any]:
        """디렉토리 조회"""
        return await self.call_tool("list_directory", {"path": path})

    async def search_files(
        self, directory: str, pattern: str = "*", recursive: bool = True
    ) -> Dict[str, Any]:
        """파일 검색"""
        return await self.call_tool(
            "search_files",
            {"directory": directory, "pattern": pattern, "recursive": recursive}
        )

    async def close(self):
        """클라이언트 종료"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
