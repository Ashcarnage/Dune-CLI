from pathlib import Path
from typing import Any, Dict
import os

from . import Tool, ToolRegistry

# Assume the workspace root is the parent directory of where the script is running
# This is a bit of a heuristic, but works for our current project structure.
WORKSPACE_ROOT = Path(os.getcwd()).parent

@ToolRegistry.register
class ReadFileTool(Tool):
    """Read the contents of a text file relative to the workspace."""

    name = "read_file"
    description = "Read the contents of a file. Args: path (str) relative path from the project root."
    schema: Dict[str, Any] = {
        "name": "read_file",
        "description": "Read the contents of a file. Args: path (str) relative path from the project root.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"}
            },
            "required": ["path"]
        }
    }

    def run(self, *, path: str, max_bytes: int | None = 10000, **kwargs) -> Any:  # noqa: D401
        file_path = WORKSPACE_ROOT / path
        
        if not file_path.exists():
            return {"error": f"File '{path}' does not exist at '{file_path}'."}
        try:
            data = file_path.read_bytes()
            if max_bytes is not None:
                data = data[:max_bytes]
            return {"contents": data.decode(errors="replace")}
        except Exception as e:
            return {"error": str(e)} 