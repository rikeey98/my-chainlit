#!/usr/bin/env python3
"""
FastMCP Server - 파일 읽기 MCP 서버
SSE (Server-Sent Events) 방식으로 read_file 도구를 제공합니다.
"""

import os
from pathlib import Path
from typing import Optional
from fastmcp import FastMCP

# FastMCP 서버 초기화
mcp = FastMCP("File Reader MCP Server")


@mcp.tool()
def read_file(path: str, encoding: str = "utf-8") -> dict:
    """
    파일 내용을 읽습니다.

    Args:
        path: 읽을 파일의 전체 경로
        encoding: 파일 인코딩 (기본값: utf-8)

    Returns:
        파일 내용 및 메타데이터를 포함한 딕셔너리
    """
    try:
        file_path = Path(path)

        # 파일 존재 여부 확인
        if not file_path.exists():
            return {
                "success": False,
                "error": f"File not found: {path}"
            }

        if not file_path.is_file():
            return {
                "success": False,
                "error": f"Not a file: {path}"
            }

        # 파일 읽기
        try:
            content = file_path.read_text(encoding=encoding)
            stat = file_path.stat()

            return {
                "success": True,
                "path": str(file_path.resolve()),
                "content": content,
                "size": stat.st_size,
                "lines": len(content.splitlines()),
                "encoding": encoding
            }
        except UnicodeDecodeError:
            return {
                "success": False,
                "error": f"Cannot decode file with {encoding} encoding. File may be binary."
            }
        except PermissionError:
            return {
                "success": False,
                "error": f"Permission denied: {path}"
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error reading file: {str(e)}"
        }


@mcp.tool()
def list_directory(path: str) -> dict:
    """
    디렉토리 내용을 나열합니다.

    Args:
        path: 조회할 디렉토리 경로

    Returns:
        디렉토리 내용을 포함한 딕셔너리
    """
    try:
        dir_path = Path(path)

        if not dir_path.exists():
            return {
                "success": False,
                "error": f"Directory not found: {path}"
            }

        if not dir_path.is_dir():
            return {
                "success": False,
                "error": f"Not a directory: {path}"
            }

        items = []
        for item in sorted(dir_path.iterdir()):
            try:
                stat = item.stat()
                items.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file",
                    "size": stat.st_size if item.is_file() else 0,
                })
            except (PermissionError, OSError) as e:
                items.append({
                    "name": item.name,
                    "error": str(e)
                })

        return {
            "success": True,
            "path": str(dir_path.resolve()),
            "items": items,
            "count": len(items)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error listing directory: {str(e)}"
        }


@mcp.tool()
def search_files(directory: str, pattern: str = "*", recursive: bool = True) -> dict:
    """
    디렉토리에서 파일을 검색합니다.

    Args:
        directory: 검색할 디렉토리
        pattern: 파일 패턴 (예: "*.py", "*.txt")
        recursive: 하위 디렉토리 포함 여부

    Returns:
        검색된 파일 목록
    """
    try:
        dir_path = Path(directory)

        if not dir_path.exists():
            return {
                "success": False,
                "error": f"Directory not found: {directory}"
            }

        if not dir_path.is_dir():
            return {
                "success": False,
                "error": f"Not a directory: {directory}"
            }

        # 파일 검색
        if recursive:
            files = list(dir_path.rglob(pattern))
        else:
            files = list(dir_path.glob(pattern))

        # 파일만 필터링
        files = [f for f in files if f.is_file()]

        file_list = []
        for file in files[:100]:  # 최대 100개로 제한
            stat = file.stat()
            file_list.append({
                "path": str(file),
                "name": file.name,
                "size": stat.st_size,
            })

        return {
            "success": True,
            "directory": str(dir_path.resolve()),
            "pattern": pattern,
            "recursive": recursive,
            "found": len(file_list),
            "files": file_list
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error searching files: {str(e)}"
        }


if __name__ == "__main__":
    # SSE 방식으로 서버 실행
    print("🚀 Starting FastMCP Server (SSE mode)")
    print("   URL: http://localhost:8100")
    print("   Press CTRL+C to stop")
    print()
    print("Available tools:")
    print("  - read_file: 파일 내용 읽기")
    print("  - list_directory: 디렉토리 내용 조회")
    print("  - search_files: 파일 검색")
    print()

    # FastMCP는 SSE 엔드포인트를 자동으로 생성합니다
    mcp.run(transport="sse", port=8100, host="0.0.0.0")
