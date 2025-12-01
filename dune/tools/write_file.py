from pathlib import Path
from typing import Any, Dict, Optional
from rich.console import Console
from rich.prompt import Prompt
import os

from . import Tool, ToolRegistry

WORKSPACE_ROOT = Path(os.getcwd())

@ToolRegistry.register
class WriteFileTool(Tool):
    """Write contents to a text file relative to the workspace."""

    name = "write_file"
    description = "Write contents to a file. Args: path (str) relative path, contents (str)."
    schema: Dict[str, Any] = {
        "name": "write_file",
        "description": "Write contents to a file. Args: path (str), contents (str).",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "contents": {"type": "string"}
            },
            "required": ["path", "contents"]
        }
    }

    def run(self, *, path: str, contents: str, yolo: bool = False, console: Optional[Console] = None, **kwargs) -> Any:
        file_path = Path(path)
        if not console:
            console = Console()

        if file_path.exists() and not yolo:
            console.print(f"File '[bold yellow]{path}[/bold yellow]' already exists.")
            if Prompt.ask("Overwrite it?", choices=["y", "n"], default="n") != "y":
                return {"error": "User chose not to overwrite the file."}
        
        try:
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(contents)
            return {"success": True, "path": str(file_path)}
        except Exception as e:
            return {"error": str(e)} 