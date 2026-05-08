"""Utility functions for CodeReview-Agent."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger


def hash_code(code: str) -> str:
    """Generate a hash for code content."""
    return hashlib.sha256(code.encode()).hexdigest()


def read_file(file_path: str) -> str:
    """Read file content safely."""
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise


def write_file(file_path: str, content: str) -> None:
    """Write content to file safely."""
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Error writing file {file_path}: {e}")
        raise


def load_json(file_path: str) -> Dict[str, Any]:
    """Load JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
        raise


def save_json(file_path: str, data: Dict[str, Any], indent: int = 2) -> None:
    """Save data to JSON file."""
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, default=str)
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")
        raise


def get_file_extension(file_path: str) -> str:
    """Get file extension without dot."""
    return Path(file_path).suffix.lstrip(".")


def detect_language(file_path: str) -> Optional[str]:
    """Detect programming language from file extension."""
    extension_map = {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "jsx": "javascript",
        "tsx": "typescript",
        "java": "java",
        "go": "go",
        "rs": "rust",
        "cpp": "cpp",
        "c": "c",
        "cs": "csharp",
        "rb": "ruby",
        "php": "php",
        "swift": "swift",
        "kt": "kotlin",
    }
    
    ext = get_file_extension(file_path)
    return extension_map.get(ext)


def calculate_file_size(file_path: str) -> int:
    """Calculate file size in bytes."""
    return Path(file_path).stat().st_size


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format timestamp in ISO format."""
    if dt is None:
        dt = datetime.utcnow()
    return dt.isoformat()


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_code_blocks(markdown: str) -> List[Dict[str, str]]:
    """Extract code blocks from markdown text."""
    import re
    
    pattern = r"```(\w+)?\n(.*?)```"
    matches = re.findall(pattern, markdown, re.DOTALL)
    
    blocks = []
    for language, code in matches:
        blocks.append({
            "language": language or "text",
            "code": code.strip()
        })
    
    return blocks


def normalize_line_endings(text: str) -> str:
    """Normalize line endings to \n."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def count_lines(code: str) -> int:
    """Count number of lines in code."""
    return len(code.splitlines())


def calculate_cyclomatic_complexity(code: str, language: str = "python") -> int:
    """Calculate cyclomatic complexity (basic implementation)."""
    if language != "python":
        return 0
    
    try:
        from radon.complexity import cc_visit
        
        results = cc_visit(code)
        if not results:
            return 1
        
        return max(func.complexity for func in results)
    except Exception as e:
        logger.warning(f"Error calculating complexity: {e}")
        return 0


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    import re
    
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename


class Timer:
    """Simple context manager for timing operations."""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        logger.debug(f"{self.name} started")
        return self
    
    def __exit__(self, *args):
        self.end_time = datetime.utcnow()
        duration = (self.end_time - self.start_time).total_seconds()
        logger.debug(f"{self.name} completed in {duration:.2f}s")
    
    @property
    def duration(self) -> float:
        """Get duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
