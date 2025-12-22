@echo off
REM FastMCP 서버와 Chainlit 앱 실행 스크립트 (Windows)

echo =========================================
echo   File MCP Agent Launcher
echo =========================================
echo.

REM Python 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python이 설치되지 않았거나 PATH에 없습니다.
    pause
    exit /b 1
)

REM 로그 디렉토리 생성
if not exist logs mkdir logs

echo [1/2] Starting MCP Server...
start /B python mcp_server.py > logs\mcp_server.log 2>&1
timeout /t 3 /nobreak >nul
echo   [OK] MCP Server started

echo.
echo [2/2] Starting Chainlit App...
echo   Opening http://localhost:8000
echo   MCP Server logs: logs\mcp_server.log
echo.
echo Press CTRL+C to stop both servers
echo.

REM Chainlit 실행
chainlit run app_mcp.py -w --port 8000

REM 정리
echo.
echo Stopping MCP Server...
taskkill /F /FI "CommandLine eq *mcp_server.py*" >nul 2>&1

pause
