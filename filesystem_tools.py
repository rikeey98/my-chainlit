"""
Local Filesystem MCP Tools
Windows, Linux, macOS에서 파일 및 디렉토리를 읽고 쓰고 수정할 수 있는 도구 모음
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class FileSystemTools:
    """로컬 파일 시스템 작업을 위한 MCP 도구"""

    def __init__(self, safe_mode: bool = True, allowed_paths: Optional[List[str]] = None):
        """
        Args:
            safe_mode: 안전 모드 활성화 (위험한 작업 제한)
            allowed_paths: 허용된 경로 목록 (None이면 모든 경로 허용)
        """
        self.safe_mode = safe_mode
        self.allowed_paths = allowed_paths or []

    def _is_path_allowed(self, path: str) -> bool:
        """경로가 허용된 경로인지 확인"""
        if not self.allowed_paths:
            return True

        abs_path = Path(path).resolve()
        for allowed in self.allowed_paths:
            allowed_abs = Path(allowed).resolve()
            try:
                abs_path.relative_to(allowed_abs)
                return True
            except ValueError:
                continue
        return False

    def _format_size(self, size_bytes: int) -> str:
        """파일 크기를 읽기 쉬운 형식으로 변환"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def list_directory(self, path: str, show_hidden: bool = False) -> Dict[str, Any]:
        """
        디렉토리 내용 조회

        Args:
            path: 조회할 디렉토리 경로
            show_hidden: 숨김 파일 표시 여부

        Returns:
            디렉토리 정보 및 내용
        """
        try:
            if not self._is_path_allowed(path):
                return {
                    "success": False,
                    "error": "Access denied: Path not in allowed paths"
                }

            path_obj = Path(path)
            if not path_obj.exists():
                return {"success": False, "error": f"Path does not exist: {path}"}

            if not path_obj.is_dir():
                return {"success": False, "error": f"Not a directory: {path}"}

            items = []
            for item in path_obj.iterdir():
                # 숨김 파일 필터링
                if not show_hidden and item.name.startswith('.'):
                    continue

                try:
                    stat = item.stat()
                    items.append({
                        "name": item.name,
                        "path": str(item),
                        "type": "directory" if item.is_dir() else "file",
                        "size": stat.st_size if item.is_file() else 0,
                        "size_formatted": self._format_size(stat.st_size) if item.is_file() else "-",
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    })
                except (PermissionError, OSError) as e:
                    items.append({
                        "name": item.name,
                        "path": str(item),
                        "type": "unknown",
                        "error": str(e)
                    })

            # 정렬: 디렉토리 먼저, 그 다음 파일 (이름순)
            items.sort(key=lambda x: (x.get("type") != "directory", x.get("name", "").lower()))

            return {
                "success": True,
                "path": str(path_obj.resolve()),
                "parent": str(path_obj.parent.resolve()) if path_obj.parent != path_obj else None,
                "total_items": len(items),
                "items": items
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def read_file(self, path: str, encoding: str = "utf-8", max_size_mb: int = 10) -> Dict[str, Any]:
        """
        파일 내용 읽기

        Args:
            path: 읽을 파일 경로
            encoding: 파일 인코딩
            max_size_mb: 최대 파일 크기 (MB)

        Returns:
            파일 내용 및 메타데이터
        """
        try:
            if not self._is_path_allowed(path):
                return {"success": False, "error": "Access denied"}

            path_obj = Path(path)
            if not path_obj.exists():
                return {"success": False, "error": f"File does not exist: {path}"}

            if not path_obj.is_file():
                return {"success": False, "error": f"Not a file: {path}"}

            # 파일 크기 확인
            size = path_obj.stat().st_size
            if size > max_size_mb * 1024 * 1024:
                return {
                    "success": False,
                    "error": f"File too large: {self._format_size(size)} (max: {max_size_mb}MB)"
                }

            # 파일 읽기
            try:
                content = path_obj.read_text(encoding=encoding)
                is_text = True
            except UnicodeDecodeError:
                # 바이너리 파일
                content = f"[Binary file, size: {self._format_size(size)}]"
                is_text = False

            stat = path_obj.stat()
            return {
                "success": True,
                "path": str(path_obj.resolve()),
                "content": content,
                "is_text": is_text,
                "size": size,
                "size_formatted": self._format_size(size),
                "encoding": encoding if is_text else "binary",
                "lines": len(content.splitlines()) if is_text else 0,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def read_multiple_files(self, paths: List[str], encoding: str = "utf-8",
                           max_size_mb: int = 10) -> Dict[str, Any]:
        """
        여러 파일을 한번에 읽기

        Args:
            paths: 읽을 파일 경로 리스트
            encoding: 파일 인코딩
            max_size_mb: 파일당 최대 크기 (MB)

        Returns:
            각 파일의 내용 및 메타데이터
        """
        try:
            if not paths:
                return {"success": False, "error": "No paths provided"}

            if len(paths) > 50:
                return {
                    "success": False,
                    "error": f"Too many files requested: {len(paths)} (max: 50)"
                }

            results = []
            success_count = 0
            failed_count = 0

            for path in paths:
                result = self.read_file(path, encoding, max_size_mb)
                if result.get("success"):
                    success_count += 1
                else:
                    failed_count += 1
                results.append({
                    "path": path,
                    "result": result
                })

            return {
                "success": True,
                "total_files": len(paths),
                "successful": success_count,
                "failed": failed_count,
                "files": results
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_files(self, directory: str, pattern: str = "*",
                    recursive: bool = True, max_files: int = 100) -> Dict[str, Any]:
        """
        디렉토리에서 파일 검색

        Args:
            directory: 검색할 디렉토리
            pattern: 파일 패턴 (예: "*.txt", "*.py")
            recursive: 하위 디렉토리 포함
            max_files: 최대 결과 개수

        Returns:
            검색된 파일 목록
        """
        try:
            if not self._is_path_allowed(directory):
                return {"success": False, "error": "Access denied"}

            dir_obj = Path(directory)
            if not dir_obj.exists():
                return {"success": False, "error": f"Directory does not exist: {directory}"}

            if not dir_obj.is_dir():
                return {"success": False, "error": f"Not a directory: {directory}"}

            # 파일 검색
            if recursive:
                files = list(dir_obj.rglob(pattern))[:max_files]
            else:
                files = list(dir_obj.glob(pattern))[:max_files]

            # 파일만 필터링
            files = [f for f in files if f.is_file()]

            file_list = []
            for file in files:
                stat = file.stat()
                file_list.append({
                    "path": str(file),
                    "name": file.name,
                    "size": stat.st_size,
                    "size_formatted": self._format_size(stat.st_size),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })

            return {
                "success": True,
                "directory": str(dir_obj.resolve()),
                "pattern": pattern,
                "recursive": recursive,
                "total_found": len(file_list),
                "files": file_list
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def write_file(self, path: str, content: str, encoding: str = "utf-8",
                   create_dirs: bool = True, overwrite: bool = False) -> Dict[str, Any]:
        """
        파일 쓰기/생성

        Args:
            path: 쓸 파일 경로
            content: 파일 내용
            encoding: 파일 인코딩
            create_dirs: 상위 디렉토리 자동 생성
            overwrite: 기존 파일 덮어쓰기 허용

        Returns:
            작업 결과
        """
        try:
            if not self._is_path_allowed(path):
                return {"success": False, "error": "Access denied"}

            path_obj = Path(path)

            # 기존 파일 확인
            if path_obj.exists() and not overwrite:
                return {
                    "success": False,
                    "error": f"File already exists: {path} (set overwrite=True to replace)"
                }

            # 디렉토리 생성
            if create_dirs:
                path_obj.parent.mkdir(parents=True, exist_ok=True)

            # 파일 쓰기
            path_obj.write_text(content, encoding=encoding)

            stat = path_obj.stat()
            return {
                "success": True,
                "path": str(path_obj.resolve()),
                "size": stat.st_size,
                "size_formatted": self._format_size(stat.st_size),
                "lines": len(content.splitlines()),
                "action": "overwritten" if overwrite and path_obj.exists() else "created"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_file(self, path: str, search: str, replace: str,
                   encoding: str = "utf-8") -> Dict[str, Any]:
        """
        파일 내용 수정 (검색 및 바꾸기)

        Args:
            path: 수정할 파일 경로
            search: 검색할 문자열
            replace: 바꿀 문자열
            encoding: 파일 인코딩

        Returns:
            수정 결과
        """
        try:
            if not self._is_path_allowed(path):
                return {"success": False, "error": "Access denied"}

            path_obj = Path(path)
            if not path_obj.exists():
                return {"success": False, "error": f"File does not exist: {path}"}

            # 파일 읽기
            content = path_obj.read_text(encoding=encoding)

            # 바꾸기
            occurrences = content.count(search)
            if occurrences == 0:
                return {
                    "success": False,
                    "error": f"Search string not found: '{search}'"
                }

            new_content = content.replace(search, replace)

            # 파일 쓰기
            path_obj.write_text(new_content, encoding=encoding)

            return {
                "success": True,
                "path": str(path_obj.resolve()),
                "occurrences_replaced": occurrences,
                "lines_before": len(content.splitlines()),
                "lines_after": len(new_content.splitlines())
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_item(self, path: str, recursive: bool = False) -> Dict[str, Any]:
        """
        파일 또는 디렉토리 삭제

        Args:
            path: 삭제할 경로
            recursive: 디렉토리 재귀 삭제 허용

        Returns:
            삭제 결과
        """
        try:
            if self.safe_mode:
                return {
                    "success": False,
                    "error": "Delete operation disabled in safe mode"
                }

            if not self._is_path_allowed(path):
                return {"success": False, "error": "Access denied"}

            path_obj = Path(path)
            if not path_obj.exists():
                return {"success": False, "error": f"Path does not exist: {path}"}

            item_type = "directory" if path_obj.is_dir() else "file"

            if path_obj.is_dir():
                if not recursive:
                    return {
                        "success": False,
                        "error": "Use recursive=True to delete directories"
                    }
                shutil.rmtree(path_obj)
            else:
                path_obj.unlink()

            return {
                "success": True,
                "path": str(path_obj.resolve()),
                "type": item_type,
                "action": "deleted"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_directory(self, path: str, parents: bool = True) -> Dict[str, Any]:
        """
        디렉토리 생성

        Args:
            path: 생성할 디렉토리 경로
            parents: 상위 디렉토리도 생성

        Returns:
            생성 결과
        """
        try:
            if not self._is_path_allowed(path):
                return {"success": False, "error": "Access denied"}

            path_obj = Path(path)
            if path_obj.exists():
                return {"success": False, "error": f"Path already exists: {path}"}

            path_obj.mkdir(parents=parents, exist_ok=False)

            return {
                "success": True,
                "path": str(path_obj.resolve()),
                "action": "created"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def move_item(self, source: str, destination: str) -> Dict[str, Any]:
        """
        파일 또는 디렉토리 이동/이름 변경

        Args:
            source: 원본 경로
            destination: 대상 경로

        Returns:
            이동 결과
        """
        try:
            if not self._is_path_allowed(source) or not self._is_path_allowed(destination):
                return {"success": False, "error": "Access denied"}

            source_obj = Path(source)
            dest_obj = Path(destination)

            if not source_obj.exists():
                return {"success": False, "error": f"Source does not exist: {source}"}

            if dest_obj.exists():
                return {"success": False, "error": f"Destination already exists: {destination}"}

            shutil.move(str(source_obj), str(dest_obj))

            return {
                "success": True,
                "source": str(source_obj.resolve()),
                "destination": str(dest_obj.resolve()),
                "action": "moved"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def copy_item(self, source: str, destination: str, overwrite: bool = False) -> Dict[str, Any]:
        """
        파일 또는 디렉토리 복사

        Args:
            source: 원본 경로
            destination: 대상 경로
            overwrite: 기존 파일 덮어쓰기

        Returns:
            복사 결과
        """
        try:
            if not self._is_path_allowed(source) or not self._is_path_allowed(destination):
                return {"success": False, "error": "Access denied"}

            source_obj = Path(source)
            dest_obj = Path(destination)

            if not source_obj.exists():
                return {"success": False, "error": f"Source does not exist: {source}"}

            if dest_obj.exists() and not overwrite:
                return {
                    "success": False,
                    "error": f"Destination already exists: {destination} (set overwrite=True)"
                }

            if source_obj.is_dir():
                if dest_obj.exists():
                    shutil.rmtree(dest_obj)
                shutil.copytree(source_obj, dest_obj)
            else:
                shutil.copy2(source_obj, dest_obj)

            return {
                "success": True,
                "source": str(source_obj.resolve()),
                "destination": str(dest_obj.resolve()),
                "type": "directory" if source_obj.is_dir() else "file",
                "action": "copied"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_file_info(self, path: str) -> Dict[str, Any]:
        """
        파일 또는 디렉토리 정보 조회

        Args:
            path: 조회할 경로

        Returns:
            파일/디렉토리 정보
        """
        try:
            if not self._is_path_allowed(path):
                return {"success": False, "error": "Access denied"}

            path_obj = Path(path)
            if not path_obj.exists():
                return {"success": False, "error": f"Path does not exist: {path}"}

            stat = path_obj.stat()
            is_dir = path_obj.is_dir()

            info = {
                "success": True,
                "path": str(path_obj.resolve()),
                "name": path_obj.name,
                "type": "directory" if is_dir else "file",
                "size": stat.st_size if not is_dir else 0,
                "size_formatted": self._format_size(stat.st_size) if not is_dir else "-",
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:],
            }

            # 디렉토리면 항목 개수 추가
            if is_dir:
                try:
                    items = list(path_obj.iterdir())
                    info["item_count"] = len(items)
                    info["subdirs"] = sum(1 for i in items if i.is_dir())
                    info["files"] = sum(1 for i in items if i.is_file())
                except PermissionError:
                    info["item_count"] = "Permission denied"

            # 파일이면 확장자 추가
            if not is_dir:
                info["extension"] = path_obj.suffix
                info["stem"] = path_obj.stem

            return info

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_tool_definitions() -> List[Dict[str, Any]]:
        """LLM이 사용할 도구 정의 반환"""
        return [
            {
                "name": "list_directory",
                "description": "디렉토리 내용을 조회합니다. 파일과 디렉토리 목록을 반환합니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "조회할 디렉토리 경로 (예: C:\\Users\\username\\Documents 또는 /home/user)"
                        },
                        "show_hidden": {
                            "type": "boolean",
                            "description": "숨김 파일 표시 여부",
                            "default": False
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "read_file",
                "description": "파일 내용을 읽습니다. 텍스트 파일의 전체 내용을 반환합니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "읽을 파일의 전체 경로"
                        },
                        "encoding": {
                            "type": "string",
                            "description": "파일 인코딩 (기본값: utf-8)",
                            "default": "utf-8"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "파일을 생성하거나 내용을 씁니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "쓸 파일의 전체 경로"
                        },
                        "content": {
                            "type": "string",
                            "description": "파일에 쓸 내용"
                        },
                        "overwrite": {
                            "type": "boolean",
                            "description": "기존 파일 덮어쓰기 허용",
                            "default": False
                        }
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "update_file",
                "description": "파일 내용을 검색하여 바꿉니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "수정할 파일 경로"
                        },
                        "search": {
                            "type": "string",
                            "description": "검색할 문자열"
                        },
                        "replace": {
                            "type": "string",
                            "description": "바꿀 문자열"
                        }
                    },
                    "required": ["path", "search", "replace"]
                }
            },
            {
                "name": "create_directory",
                "description": "새 디렉토리를 생성합니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "생성할 디렉토리 경로"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "get_file_info",
                "description": "파일이나 디렉토리의 상세 정보를 조회합니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "정보를 조회할 경로"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "copy_item",
                "description": "파일이나 디렉토리를 복사합니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "source": {
                            "type": "string",
                            "description": "원본 경로"
                        },
                        "destination": {
                            "type": "string",
                            "description": "대상 경로"
                        },
                        "overwrite": {
                            "type": "boolean",
                            "description": "기존 파일 덮어쓰기",
                            "default": False
                        }
                    },
                    "required": ["source", "destination"]
                }
            },
            {
                "name": "move_item",
                "description": "파일이나 디렉토리를 이동하거나 이름을 변경합니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "source": {
                            "type": "string",
                            "description": "원본 경로"
                        },
                        "destination": {
                            "type": "string",
                            "description": "대상 경로"
                        }
                    },
                    "required": ["source", "destination"]
                }
            },
            {
                "name": "read_multiple_files",
                "description": "여러 파일을 한번에 읽습니다. 최대 50개 파일까지 가능합니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "paths": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "읽을 파일 경로 목록 (최대 50개)"
                        },
                        "encoding": {
                            "type": "string",
                            "description": "파일 인코딩 (기본값: utf-8)",
                            "default": "utf-8"
                        }
                    },
                    "required": ["paths"]
                }
            },
            {
                "name": "search_files",
                "description": "디렉토리에서 파일을 검색합니다. 파일 패턴(예: *.txt, *.py)으로 검색할 수 있습니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "검색할 디렉토리 경로"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "파일 패턴 (예: '*.txt', '*.py', 'test_*.py')",
                            "default": "*"
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "하위 디렉토리 포함 여부",
                            "default": True
                        },
                        "max_files": {
                            "type": "integer",
                            "description": "최대 결과 개수",
                            "default": 100
                        }
                    },
                    "required": ["directory"]
                }
            }
        ]
