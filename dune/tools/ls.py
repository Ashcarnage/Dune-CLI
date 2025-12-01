import os
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

from . import Tool, ToolRegistry

@ToolRegistry.register
class LsTool(Tool):
    """
    Lists the contents of a directory with detailed information.
    """
    name = "ls"
    description = "List the contents of a directory, similar to the `ls -l` command."
    schema: Dict[str, Any] = {
        "name": "ls",
        "description": "List the contents of a directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path to the directory to list. Defaults to the current directory."
                }
            },
            "required": []
        }
    }

    def run(self, *, path: str = ".", **kwargs) -> Any:
        try:
            p = Path(path)
            if not p.is_dir():
                return {"error": f"Path '{path}' is not a valid directory."}

            results = []
            for item in p.iterdir():
                try:
                    stat = item.stat()
                    results.append({
                        "name": item.name,
                        "type": "dir" if item.is_dir() else "file",
                        "size": stat.st_size,
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })
                except OSError:
                    # Could happen for broken symlinks, etc.
                    results.append({"name": item.name, "type": "unknown", "error": "Could not stat file"})
            
            # Sort by name for consistent output
            results.sort(key=lambda x: x['name'])
            return {"files": results}
            
        except Exception as e:
            return {"error": str(e)} 