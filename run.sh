#!/bin/bash

# LLM Chat Web Application 실행 스크립트

echo "🚀 Starting LLM Chat Application..."
echo ""

# .env 파일 확인
if [ ! -f .env ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 복사하여 .env 파일을 생성하세요."
    echo ""
    echo "다음 명령을 실행하세요:"
    echo "  cp .env.example .env"
    echo "  # 그 다음 .env 파일을 편집하세요"
    exit 1
fi

# 의존성 확인
if ! command -v chainlit &> /dev/null; then
    echo "⚠️  Chainlit이 설치되지 않았습니다."
    echo ""
    echo "다음 명령으로 설치하세요:"
    echo "  pip install -r requirements.txt"
    exit 1
fi

echo "✅ 환경 설정 확인 완료"
echo ""
echo "📝 설정 정보:"
source .env
echo "  - API Base: ${OPENAI_API_BASE}"
echo "  - Model: ${MODEL_NAME}"
echo "  - MCP Enabled: ${MCP_SERVER_ENABLED}"
if [ "$MCP_SERVER_ENABLED" = "true" ]; then
    echo "  - MCP Server: ${MCP_SERVER_URL}"
fi
echo ""
echo "🌐 브라우저에서 http://localhost:8000 으로 접속하세요"
echo ""
echo "Press CTRL+C to stop"
echo ""

# Chainlit 실행
chainlit run app.py -w
