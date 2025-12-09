#!/usr/bin/env python
"""
크로스 플랫폼 LLM Chat Application 실행 스크립트
Windows, Linux, macOS 모두에서 동작합니다.

사용법:
  python start.py              # 기본 실행
  python start.py --with-mcp   # MCP 서버와 함께 실행
  python start.py --help       # 도움말
"""

import os
import sys
import subprocess
import time
import signal
import argparse
from pathlib import Path
import urllib.request
import urllib.error


class Colors:
    """터미널 색상 (Windows에서는 무시될 수 있음)"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """헤더 출력"""
    print(f"\n{Colors.BOLD}{'=' * 50}{Colors.ENDC}")
    print(f"{Colors.BOLD}{text:^50}{Colors.ENDC}")
    print(f"{Colors.BOLD}{'=' * 50}{Colors.ENDC}\n")


def print_info(text):
    """정보 메시지 출력"""
    print(f"{Colors.OKBLUE}[INFO]{Colors.ENDC} {text}")


def print_success(text):
    """성공 메시지 출력"""
    print(f"{Colors.OKGREEN}[OK]{Colors.ENDC} {text}")


def print_warning(text):
    """경고 메시지 출력"""
    print(f"{Colors.WARNING}[WARNING]{Colors.ENDC} {text}")


def print_error(text):
    """에러 메시지 출력"""
    print(f"{Colors.FAIL}[ERROR]{Colors.ENDC} {text}")


def check_python():
    """Python 설치 확인"""
    print_info(f"Python version: {sys.version.split()[0]}")
    if sys.version_info < (3, 8):
        print_error("Python 3.8 이상이 필요합니다.")
        return False
    return True


def check_env_file():
    """환경 변수 파일 확인"""
    env_file = Path(".env")
    if not env_file.exists():
        print_error(".env 파일이 없습니다!")
        print_info("다음 명령을 실행하세요:")
        if os.name == 'nt':  # Windows
            print("  copy .env.example .env")
        else:  # Unix-like
            print("  cp .env.example .env")
        print("  그 다음 .env 파일을 편집하세요")
        return False
    return True


def check_dependencies():
    """필수 패키지 설치 확인"""
    try:
        import chainlit
        print_success("Chainlit 설치 확인됨")
        return True
    except ImportError:
        print_warning("Chainlit이 설치되지 않았습니다.")
        print_info("다음 명령으로 설치하세요:")
        print("  pip install -r requirements.txt")
        return False


def load_env():
    """환경 변수 로드 및 출력"""
    env_vars = {}
    try:
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()
    except Exception as e:
        print_warning(f".env 파일 읽기 실패: {e}")

    return env_vars


def print_config(env_vars):
    """설정 정보 출력"""
    print("\n설정 정보:")
    print(f"  - API Base: {env_vars.get('OPENAI_API_BASE', 'Not set')}")
    print(f"  - Model: {env_vars.get('MODEL_NAME', 'Not set')}")
    print(f"  - MCP Enabled: {env_vars.get('MCP_SERVER_ENABLED', 'false')}")
    if env_vars.get('MCP_SERVER_ENABLED', '').lower() == 'true':
        print(f"  - MCP Server: {env_vars.get('MCP_SERVER_URL', 'Not set')}")


def check_mcp_health(url):
    """MCP 서버 헬스 체크"""
    try:
        response = urllib.request.urlopen(f"{url}/health", timeout=5)
        return response.status == 200
    except Exception:
        return False


def start_mcp_server():
    """MCP 서버 시작"""
    print_info("Starting MCP Server on port 3000...")

    # 로그 디렉토리 생성
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "mcp_server.log"

    # MCP 서버 시작
    with open(log_file, "w") as f:
        if os.name == 'nt':  # Windows
            process = subprocess.Popen(
                ["python", "mcp_server_example.py"],
                stdout=f,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:  # Unix-like
            process = subprocess.Popen(
                ["python", "mcp_server_example.py"],
                stdout=f,
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid
            )

    # 서버 시작 대기
    print_info("Waiting for MCP Server to start...")
    time.sleep(3)

    # 헬스 체크
    if check_mcp_health("http://localhost:3000"):
        print_success("MCP Server started successfully")
    else:
        print_warning("MCP Server may not be running properly")
        print_info(f"Check logs: {log_file}")

    return process


def start_chainlit():
    """Chainlit 애플리케이션 시작"""
    print_info("Starting Chainlit Application...")
    print_info("브라우저에서 http://localhost:8000 으로 접속하세요")
    print_info("종료하려면 CTRL+C를 누르세요\n")

    try:
        subprocess.run(["chainlit", "run", "app.py", "-w"], check=True)
    except KeyboardInterrupt:
        print_info("\nShutting down...")
    except subprocess.CalledProcessError as e:
        print_error(f"Chainlit 실행 실패: {e}")


def cleanup_mcp_server(process):
    """MCP 서버 정리"""
    if process:
        print_info("Stopping MCP Server...")
        try:
            if os.name == 'nt':  # Windows
                process.terminate()
            else:  # Unix-like
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)

            process.wait(timeout=5)
            print_success("MCP Server stopped")
        except Exception as e:
            print_warning(f"MCP Server 종료 중 오류: {e}")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="LLM Chat Application 실행 스크립트"
    )
    parser.add_argument(
        "--with-mcp",
        action="store_true",
        help="MCP 서버와 함께 실행"
    )
    args = parser.parse_args()

    # 헤더 출력
    if args.with_mcp:
        print_header("LLM Chat + MCP Server")
    else:
        print_header("LLM Chat Application")

    # 환경 확인
    if not check_python():
        return 1

    if not check_env_file():
        return 1

    if not check_dependencies():
        return 1

    print_success("환경 설정 확인 완료")

    # 환경 변수 로드
    env_vars = load_env()
    print_config(env_vars)

    # MCP 서버 시작 (옵션)
    mcp_process = None
    if args.with_mcp:
        # MCP 활성화 확인
        if env_vars.get('MCP_SERVER_ENABLED', '').lower() != 'true':
            print_warning("MCP가 비활성화되어 있습니다.")
            print_info(".env 파일에서 MCP_SERVER_ENABLED=true로 설정하세요.")
            return 1

        mcp_process = start_mcp_server()
        print_info(f"MCP Server 로그: logs/mcp_server.log")

    # Chainlit 시작
    print()
    try:
        start_chainlit()
    finally:
        # MCP 서버 정리
        if mcp_process:
            cleanup_mcp_server(mcp_process)

    return 0


if __name__ == "__main__":
    sys.exit(main())
