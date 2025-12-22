# 🤖 File MCP Agent - Chainlit + FastMCP SSE

FastMCP SSE 방식을 사용한 파일 읽기 MCP 에이전트입니다.

## ✨ 주요 기능

- 💬 **Chainlit 채팅 UI**: 직관적인 채팅 인터페이스
- 🔧 **FastMCP SSE**: Server-Sent Events 방식의 MCP 서버
- 📁 **파일 시스템 도구**: 파일 읽기, 디렉토리 조회, 파일 검색
- 🤖 **LLM 통합**: OpenAI compatible API 지원

## 📋 기술 스택

- **환경**: Linux, uv (또는 pip)
- **UI**: Chainlit
- **LLM**: OpenAI Compatible API
- **MCP**: FastMCP SSE (파일 읽기 도구)

## 🏗️ 프로젝트 구조

```
my-chainlit/
├── pyproject.toml        # uv 프로젝트 설정
├── .env.mcp              # 환경 변수
├── mcp_server.py         # FastMCP 파일 읽기 서버
├── mcp_client.py         # SSE 클라이언트
├── app_mcp.py            # Chainlit 메인 앱
├── run_mcp.sh            # Linux/macOS 실행 스크립트
├── run_mcp.bat           # Windows 실행 스크립트
└── README_MCP.md         # 이 파일
```

## 🚀 빠른 시작

### 1. 의존성 설치

#### uv 사용 (권장)
```bash
# uv 설치 (아직 없다면)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성 설치
uv sync
```

#### pip 사용
```bash
pip install -r requirements.txt

# 추가 패키지 설치
pip install fastmcp httpx httpx-sse
```

### 2. 환경 설정

`.env.mcp` 파일을 편집하세요:

```bash
# OpenAI Compatible API 설정
OPENAI_API_BASE=http://localhost:8000/v1
OPENAI_API_KEY=your-api-key-here
MODEL_NAME=gpt-4

# MCP Server 설정
MCP_SERVER_URL=http://localhost:8100
```

### 3. 실행

#### 방법 1: 실행 스크립트 사용 (권장)

**Linux/macOS:**
```bash
./run_mcp.sh
```

**Windows:**
```cmd
run_mcp.bat
```

#### 방법 2: 수동 실행

**터미널 1 - MCP 서버:**
```bash
python mcp_server.py
```

**터미널 2 - Chainlit 앱:**
```bash
chainlit run app_mcp.py -w --port 8000
```

브라우저에서 http://localhost:8000 으로 접속합니다.

## 🔧 MCP 서버 (mcp_server.py)

FastMCP를 사용한 SSE 방식 MCP 서버입니다.

### 제공하는 도구

| 도구 | 설명 | 파라미터 |
|------|------|----------|
| `read_file` | 파일 내용 읽기 | path, encoding |
| `list_directory` | 디렉토리 조회 | path |
| `search_files` | 파일 검색 | directory, pattern, recursive |

### 실행

```bash
python mcp_server.py
```

기본적으로 `http://localhost:8100`에서 실행됩니다.

### API 엔드포인트

- `GET /tools` - 도구 목록
- `POST /sse` - SSE 스트림 (도구 호출)

## 📡 MCP 클라이언트 (mcp_client.py)

SSE 방식으로 FastMCP 서버와 통신하는 클라이언트입니다.

### 사용 예시

```python
from mcp_client import MCPClient

async with MCPClient("http://localhost:8100") as mcp:
    # 파일 읽기
    result = await mcp.read_file("README.md")
    print(result["content"])

    # 디렉토리 조회
    result = await mcp.list_directory(".")
    print(result["items"])

    # 파일 검색
    result = await mcp.search_files(".", "*.py")
    print(result["files"])
```

## 💬 Chainlit 앱 (app_mcp.py)

간소화된 Chainlit 애플리케이션입니다.

### 실행 흐름

1. **사용자 질문** → Chainlit UI
2. **LLM 판단** → 도구 필요 여부 결정
3. **도구 호출** → MCP 클라이언트 → MCP 서버
4. **결과 반환** → LLM → 최종 답변
5. **UI 표시** → 사용자

### 주요 기능

- 자동 MCP 도구 검색 및 LLM 통합
- 실시간 도구 실행 과정 표시
- Function Calling 지원

## 🎯 사용 예시

### 예시 1: 파일 읽기

```
사용자: README.md 파일을 읽어줘

AI: 🔧 read_file 실행 중...
    {
      "path": "README.md",
      "encoding": "utf-8"
    }
    ✅ 성공

    README.md 파일의 내용은 다음과 같습니다:
    [파일 내용 표시...]
```

### 예시 2: 디렉토리 조회

```
사용자: 현재 디렉토리의 파일 목록을 보여줘

AI: 🔧 list_directory 실행 중...
    ✅ 성공

    다음 파일들이 있습니다:
    - app_mcp.py (파일, 8.5KB)
    - mcp_server.py (파일, 6.2KB)
    - mcp_client.py (파일, 3.8KB)
    ...
```

### 예시 3: 파일 검색

```
사용자: 모든 Python 파일을 찾아줘

AI: 🔧 search_files 실행 중...
    {
      "directory": ".",
      "pattern": "*.py",
      "recursive": true
    }
    ✅ 성공

    총 15개의 Python 파일을 찾았습니다:
    - app_mcp.py
    - mcp_server.py
    - mcp_client.py
    ...
```

## 🔍 FastMCP SSE 방식

### SSE (Server-Sent Events)란?

- HTTP 스트리밍 프로토콜
- 서버에서 클라이언트로 실시간 이벤트 전송
- WebSocket보다 단순하고 HTTP 호환성 좋음

### 장점

1. **단순한 프로토콜**: HTTP 기반으로 방화벽 통과 쉬움
2. **자동 재연결**: 연결 끊김 시 자동 복구
3. **브라우저 호환**: 표준 EventSource API 지원

### 통신 흐름

```
Client → POST /sse (JSON request)
         ↓
Server → SSE Stream
         ├─ event: result
         │  data: {...}
         └─ event: error
            data: {...}
```

## 🔐 보안 고려사항

- MCP 서버는 로컬호스트에서만 실행
- 파일 접근 권한 체크
- 경로 traversal 공격 방지

## 🐛 문제 해결

### MCP 서버 연결 실패

```
❌ MCP 서버에 연결할 수 없습니다.
```

**해결방법:**
1. MCP 서버가 실행 중인지 확인: `curl http://localhost:8100/tools`
2. `.env.mcp`에서 `MCP_SERVER_URL` 확인
3. 포트 8100이 사용 가능한지 확인

### LLM API 오류

```
❌ OpenAI API error
```

**해결방법:**
1. `.env.mcp`에서 `OPENAI_API_BASE` 확인
2. API 서버가 실행 중인지 확인
3. API 키 확인 (필요한 경우)

### 의존성 오류

```bash
# FastMCP 설치
pip install fastmcp

# SSE 클라이언트 설치
pip install httpx httpx-sse

# 전체 재설치
pip install -r requirements.txt --force-reinstall
```

## 📚 참고 자료

- [FastMCP](https://github.com/jlowin/fastmcp) - FastMCP 라이브러리
- [Chainlit](https://docs.chainlit.io/) - Chainlit 문서
- [SSE](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events) - Server-Sent Events
- [httpx-sse](https://github.com/florimondmanca/httpx-sse) - HTTPX SSE 클라이언트

## 🤝 기여

이슈와 풀 리퀘스트는 언제나 환영합니다!

## 📝 라이선스

MIT License

---

Made with ❤️ using Chainlit + FastMCP
