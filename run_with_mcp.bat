@echo off
REM LLM Chat Application + MCP Server 동시 실행 스크립트 (Windows)

echo ==========================================
echo   LLM Chat + MCP Server
echo ==========================================
echo.

REM .env 파일 확인
if not exist .env (
    echo [WARNING] .env 파일이 없습니다!
    echo .env.example을 복사하여 .env 파일을 생성하세요.
    pause
    exit /b 1
)

REM Python 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python이 설치되지 않았거나 PATH에 없습니다.
    pause
    exit /b 1
)

REM Chainlit 확인
python -c "import chainlit" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Chainlit이 설치되지 않았습니다.
    echo 다음 명령으로 설치: pip install -r requirements.txt
    pause
    exit /b 1
)

REM MCP 활성화 확인
findstr /C:"MCP_SERVER_ENABLED=true" .env >nul 2>&1
if errorlevel 1 (
    echo [WARNING] MCP가 비활성화되어 있습니다.
    echo .env 파일에서 MCP_SERVER_ENABLED=true로 설정하세요.
    pause
    exit /b 1
)

echo [OK] 환경 설정 확인 완료
echo.

REM 로그 디렉토리 생성
if not exist logs mkdir logs

REM MCP 서버 백그라운드 실행
echo [1/2] Starting MCP Server on port 3000...
start /B python mcp_server_example.py > logs\mcp_server.log 2>&1

REM MCP 서버 시작 대기
timeout /t 3 /nobreak >nul

REM MCP 서버 헬스 체크
curl -s http://localhost:3000/health >nul 2>&1
if errorlevel 1 (
    echo [WARNING] MCP Server may not be running properly
) else (
    echo [OK] MCP Server started successfully
)

echo.
echo 설정 정보:
for /f "tokens=1,2 delims==" %%a in ('type .env ^| findstr /v "^#"') do (
    if "%%a"=="OPENAI_API_BASE" echo   - API Base: %%b
    if "%%a"=="MODEL_NAME" echo   - Model: %%b
    if "%%a"=="MCP_SERVER_URL" echo   - MCP Server: %%b
)
echo.
echo [INFO] 브라우저에서 http://localhost:8000 으로 접속하세요
echo [INFO] MCP Server 로그: logs\mcp_server.log
echo [INFO] 종료하려면 CTRL+C를 누르세요
echo.

REM Chainlit 실행
echo [2/2] Starting Chainlit Application...
chainlit run app.py -w

REM 정리 (사용자가 종료했을 때)
echo.
echo [INFO] Stopping MCP Server...
taskkill /F /FI "WINDOWTITLE eq mcp_server_example.py*" >nul 2>&1
taskkill /F /FI "CommandLine eq *mcp_server_example.py*" >nul 2>&1

pause
