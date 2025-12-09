@echo off
REM LLM Chat Web Application 실행 스크립트 (Windows)

echo ==========================================
echo   LLM Chat Application
echo ==========================================
echo.

REM .env 파일 확인
if not exist .env (
    echo [WARNING] .env 파일이 없습니다!
    echo.
    echo .env.example을 복사하여 .env 파일을 생성하세요:
    echo   copy .env.example .env
    echo   그 다음 .env 파일을 편집하세요
    echo.
    pause
    exit /b 1
)

REM Python 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python이 설치되지 않았거나 PATH에 없습니다.
    echo Python을 설치하고 PATH에 추가하세요.
    pause
    exit /b 1
)

REM Chainlit 확인
python -c "import chainlit" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Chainlit이 설치되지 않았습니다.
    echo.
    echo 다음 명령으로 설치하세요:
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo [OK] 환경 설정 확인 완료
echo.

REM 환경 변수 출력
echo 설정 정보:
for /f "tokens=1,2 delims==" %%a in ('type .env ^| findstr /v "^#"') do (
    if "%%a"=="OPENAI_API_BASE" echo   - API Base: %%b
    if "%%a"=="MODEL_NAME" echo   - Model: %%b
    if "%%a"=="MCP_SERVER_ENABLED" echo   - MCP Enabled: %%b
    if "%%a"=="MCP_SERVER_URL" (
        for /f "tokens=1,2 delims==" %%c in ('type .env ^| findstr "MCP_SERVER_ENABLED"') do (
            if "%%d"=="true" echo   - MCP Server: %%b
        )
    )
)
echo.
echo [INFO] 브라우저에서 http://localhost:8000 으로 접속하세요
echo [INFO] 종료하려면 CTRL+C를 누르세요
echo.

REM Chainlit 실행
chainlit run app.py -w

pause
