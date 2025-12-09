#!/bin/bash

# LLM Chat Application + MCP Server 동시 실행 스크립트

echo "🚀 Starting LLM Chat Application with MCP Server..."
echo ""

# .env 파일 확인
if [ ! -f .env ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 복사하여 .env 파일을 생성하세요."
    exit 1
fi

# 의존성 확인
if ! command -v chainlit &> /dev/null; then
    echo "⚠️  Chainlit이 설치되지 않았습니다."
    echo "다음 명령으로 설치하세요: pip install -r requirements.txt"
    exit 1
fi

# MCP 서버가 활성화되어 있는지 확인
source .env
if [ "$MCP_SERVER_ENABLED" != "true" ]; then
    echo "⚠️  MCP가 비활성화되어 있습니다."
    echo ".env 파일에서 MCP_SERVER_ENABLED=true로 설정하세요."
    exit 1
fi

echo "✅ 환경 설정 확인 완료"
echo ""

# 로그 디렉토리 생성
mkdir -p logs

# MCP 서버 백그라운드 실행
echo "🔧 Starting MCP Server on port 3000..."
python mcp_server_example.py > logs/mcp_server.log 2>&1 &
MCP_PID=$!
echo "  MCP Server PID: $MCP_PID"

# MCP 서버 시작 대기
sleep 2

# MCP 서버 헬스 체크
if curl -s http://localhost:3000/health > /dev/null 2>&1; then
    echo "✅ MCP Server started successfully"
else
    echo "⚠️  MCP Server may not be running properly"
fi

echo ""
echo "📝 설정 정보:"
echo "  - API Base: ${OPENAI_API_BASE}"
echo "  - Model: ${MODEL_NAME}"
echo "  - MCP Server: ${MCP_SERVER_URL}"
echo ""
echo "🌐 브라우저에서 http://localhost:8000 으로 접속하세요"
echo "📋 MCP Server 로그: logs/mcp_server.log"
echo ""
echo "Press CTRL+C to stop both servers"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $MCP_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Trap CTRL+C
trap cleanup INT TERM

# Chainlit 실행 (포그라운드)
chainlit run app.py -w

# Cleanup on exit
cleanup
