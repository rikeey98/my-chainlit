# 🤖 LLM Chat Web Application

Chainlit을 사용한 OpenAI Compatible API 기반 채팅 웹 애플리케이션입니다. MCP(Model Context Protocol) 서버 통합을 지원합니다.

## ✨ 주요 기능

- 💬 **실시간 스트리밍 채팅**: OpenAI compatible API를 통한 실시간 대화
- 🔌 **OpenAI Compatible API**: OpenAI API와 호환되는 모든 LLM 서비스 지원
  - OpenAI, Azure OpenAI
  - LM Studio, Ollama, LocalAI
  - vLLM, Text Generation WebUI
  - 기타 OpenAI API 호환 서비스
- 🛠️ **MCP 통합**: Model Context Protocol을 통한 컨텍스트 강화 및 도구 사용
- 🎨 **깔끔한 UI**: Chainlit 기반의 직관적인 사용자 인터페이스
- 📝 **대화 히스토리**: 세션별 대화 내용 자동 관리

## 📋 요구사항

- Python 3.8 이상
- pip 또는 conda

## 🚀 빠른 시작

### 1. 저장소 클론 및 의존성 설치

```bash
# 저장소 클론
git clone <repository-url>
cd my-chainlit

# 가상 환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 설정합니다:

```bash
cp .env.example .env
```

`.env` 파일 내용을 수정합니다:

```bash
# OpenAI Compatible API 설정
OPENAI_API_BASE=http://localhost:8000/v1  # API 엔드포인트
OPENAI_API_KEY=your-api-key-here           # API 키 (필요한 경우)
MODEL_NAME=gpt-3.5-turbo                   # 사용할 모델 이름

# MCP 서버 설정 (선택사항)
MCP_SERVER_ENABLED=false                   # MCP 사용 여부
MCP_SERVER_URL=http://localhost:3000       # MCP 서버 URL
```

### 3. 애플리케이션 실행

#### 방법 1: 크로스 플랫폼 Python 스크립트 (권장)

**기본 실행:**
```bash
python start.py
```

**MCP 서버와 함께 실행:**
```bash
python start.py --with-mcp
```

#### 방법 2: 플랫폼별 스크립트

**Linux/macOS:**
```bash
./run.sh                    # 기본 실행
./run_with_mcp.sh           # MCP와 함께 실행
```

**Windows:**
```cmd
run.bat                     # 기본 실행
run_with_mcp.bat            # MCP와 함께 실행
```

#### 방법 3: 직접 실행

```bash
chainlit run app.py -w
```

`-w` 옵션은 파일 변경 시 자동으로 재시작합니다.

브라우저에서 http://localhost:8000 으로 접속합니다.

## 🔧 OpenAI Compatible API 설정 예시

### Ollama

```bash
OPENAI_API_BASE=http://localhost:11434/v1
OPENAI_API_KEY=ollama
MODEL_NAME=llama2
```

### LM Studio

```bash
OPENAI_API_BASE=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio
MODEL_NAME=local-model
```

### vLLM

```bash
OPENAI_API_BASE=http://localhost:8000/v1
OPENAI_API_KEY=your-key
MODEL_NAME=meta-llama/Llama-2-7b-chat-hf
```

### Azure OpenAI

```bash
OPENAI_API_BASE=https://your-resource.openai.azure.com/openai/deployments/your-deployment
OPENAI_API_KEY=your-azure-key
MODEL_NAME=gpt-35-turbo
```

## 🛠️ MCP (Model Context Protocol) 사용하기

MCP를 사용하면 LLM에 추가 컨텍스트와 도구를 제공할 수 있습니다.

### MCP 서버 예시 실행

프로젝트에 포함된 예시 MCP 서버를 실행할 수 있습니다:

```bash
# 새 터미널에서 실행
python mcp_server_example.py
```

이제 `.env` 파일에서 MCP를 활성화합니다:

```bash
MCP_SERVER_ENABLED=true
MCP_SERVER_URL=http://localhost:3000
```

### MCP 서버 기능

예시 MCP 서버는 다음 기능을 제공합니다:

- **컨텍스트 제공**: 사용자 쿼리에 관련된 컨텍스트 자동 추가
- **도구 제공**:
  - `calculate`: 수학 계산
  - `web_search`: 웹 검색 (모의)
  - `get_weather`: 날씨 정보 (모의)

### 커스텀 MCP 서버 구현

`mcp_server_example.py`를 참고하여 자신만의 MCP 서버를 구현할 수 있습니다:

1. FastAPI를 사용하여 서버 생성
2. 필요한 엔드포인트 구현:
   - `GET /health`: 헬스 체크
   - `POST /context`: 컨텍스트 제공
   - `GET /tools`: 사용 가능한 도구 목록
   - `POST /tools/{tool_name}/call`: 도구 실행

## 📁 프로젝트 구조

```
my-chainlit/
├── app.py                    # 메인 Chainlit 애플리케이션
├── mcp_tools.py              # MCP 클라이언트 및 로컬 도구
├── mcp_server_example.py     # MCP 서버 예시 구현
├── chainlit.md               # 채팅 시작 화면
├── config.toml               # Chainlit 설정
├── requirements.txt          # Python 의존성
├── .env.example              # 환경 변수 예시
├── .gitignore                # Git 제외 파일
├── start.py                  # 크로스 플랫폼 실행 스크립트 (권장)
├── run.sh                    # Linux/macOS 실행 스크립트
├── run_with_mcp.sh           # Linux/macOS MCP 포함 실행 스크립트
├── run.bat                   # Windows 실행 스크립트
├── run_with_mcp.bat          # Windows MCP 포함 실행 스크립트
└── README.md                 # 이 파일
```

## 🎯 사용 예시

### 기본 대화

```
사용자: 안녕하세요!
AI: 안녕하세요! 무엇을 도와드릴까요?
```

### MCP 컨텍스트 활용 (MCP 활성화 시)

```
사용자: Python에 대해 설명해주세요
AI: [MCP에서 Python 관련 컨텍스트 자동 로드]
    Python은 고수준 인터프리터 프로그래밍 언어로...
```

### 도구 사용 (MCP 도구 활성화 시)

```
사용자: 25 * 4를 계산해주세요
AI: [calculate 도구 호출]
    25 * 4 = 100입니다.
```

## 🔒 보안 고려사항

- `.env` 파일은 반드시 `.gitignore`에 포함시켜 커밋하지 않도록 합니다
- API 키는 환경 변수로 관리하고 코드에 직접 작성하지 않습니다
- 프로덕션 환경에서는 적절한 인증 및 권한 관리를 구현해야 합니다
- MCP 서버의 도구 실행 시 입력 검증을 철저히 해야 합니다

## 🐛 문제 해결

### 연결 오류

```
Error: Connection refused
```

- OpenAI compatible API 서버가 실행 중인지 확인
- `OPENAI_API_BASE` URL이 올바른지 확인
- 방화벽 설정 확인

### MCP 서버 연결 실패

```
MCP Server connection error
```

- MCP 서버가 실행 중인지 확인
- `MCP_SERVER_URL`이 올바른지 확인
- `MCP_SERVER_ENABLED=true`로 설정되어 있는지 확인

### 패키지 설치 오류

```bash
# 최신 pip로 업그레이드
pip install --upgrade pip

# 개별 패키지 설치
pip install chainlit openai python-dotenv
```

### Windows 관련 문제

**Python이 PATH에 없는 경우:**
- Python 설치 시 "Add Python to PATH" 옵션을 선택하거나
- 수동으로 환경 변수에 Python 경로 추가

**실행 권한 문제:**
- PowerShell에서 실행 시 권한 오류가 발생하면:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

**포트 충돌:**
- 8000번 포트가 이미 사용 중이면 다른 애플리케이션을 종료하거나
- `chainlit run app.py -w --port 8001`로 다른 포트 사용

## 🎨 커스터마이징

### UI 테마 변경

`config.toml` 파일에서 색상과 레이아웃을 변경할 수 있습니다:

```toml
[UI.theme.light]
    background = "#FAFAFA"
    paper = "#FFFFFF"

    [UI.theme.light.primary]
        main = "#F80061"
```

### 시작 메시지 변경

`chainlit.md` 파일을 수정하여 채팅 시작 화면을 커스터마이징할 수 있습니다.

### 모델 파라미터 조정

`app.py`의 `client.chat.completions.create()` 호출에서 파라미터를 조정할 수 있습니다:

```python
stream = await client.chat.completions.create(
    model=MODEL_NAME,
    messages=message_history,
    stream=True,
    temperature=0.7,      # 창의성 조절 (0.0-2.0)
    max_tokens=2000,      # 최대 토큰 수
    top_p=0.9,            # Nucleus sampling
    frequency_penalty=0,  # 반복 패널티
    presence_penalty=0    # 주제 다양성
)
```

## 🤝 기여하기

이슈와 풀 리퀘스트는 언제나 환영합니다!

## 📝 라이선스

MIT License

## 🔗 참고 자료

- [Chainlit 문서](https://docs.chainlit.io/)
- [OpenAI API 문서](https://platform.openai.com/docs/api-reference)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastAPI 문서](https://fastapi.tiangolo.com/)

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 생성해주세요.

---

Made with ❤️ using Chainlit
