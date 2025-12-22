#!/bin/bash
# FastMCP 서버와 Chainlit 앱 실행 스크립트

echo "========================================="
echo "  File MCP Agent Launcher"
echo "========================================="
echo

# 환경 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3이 설치되지 않았습니다."
    exit 1
fi

# 로그 디렉토리 생성
mkdir -p logs

echo "[1/2] Starting MCP Server..."
python3 mcp_server.py > logs/mcp_server.log 2>&1 &
MCP_PID=$!
echo "  MCP Server PID: $MCP_PID"

# MCP 서버 시작 대기
sleep 3

# MCP 서버 헬스 체크
if curl -s http://localhost:8100/tools > /dev/null 2>&1; then
    echo "  ✅ MCP Server started successfully"
else
    echo "  ⚠️  MCP Server may not be running properly"
    echo "  Check logs/mcp_server.log for details"
fi

echo
echo "[2/2] Starting Chainlit App..."
echo "  🌐 Opening http://localhost:8000"
echo "  📋 MCP Server logs: logs/mcp_server.log"
echo
echo "Press CTRL+C to stop both servers"
echo

# Cleanup function
cleanup() {
    echo
    echo "🛑 Stopping servers..."
    kill $MCP_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Trap CTRL+C
trap cleanup INT TERM

# Chainlit 실행 (포그라운드)
chainlit run app_mcp.py -w --port 8000

# Cleanup on exit
cleanup
