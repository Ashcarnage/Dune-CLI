from pathlib import Path
from typing import Any, Dict, List

from . import Tool, ToolRegistry

@ToolRegistry.register
class ReadManyFilesTool(Tool):
    """
    Reads the contents of multiple text files.
    """
    name = "read_many_files"
    description = "Read the contents of multiple files."
    schema: Dict[str, Any] = {
        "name": "read_many_files",
        "description": "Read the contents of multiple files.",
        "parameters": {
            "type": "object",
            "properties": {
                "paths": {
                    "type": "array",
                    "description": "A list of file paths to read.",
                    "items": {"type": "string"}
                }
            },
            "required": ["paths"]
        }
    }

    def run(self, *, paths: List[str], **kwargs) -> Any:
        results = {}
        for path_str in paths:
            try:
                with open(path_str, 'r') as f:
                    results[path_str] = f.read()
            except Exception as e:
                results[path_str] = {"error": str(e)}
        return results 