import re
from pathlib import Path
from typing import Any, Dict, List

from . import Tool, ToolRegistry

@ToolRegistry.register
class GrepTool(Tool):
    """
    Searches for a regex pattern in a file or list of files.
    """
    name = "grep"
    description = "Search for a pattern in one or more files."
    schema: Dict[str, Any] = {
        "name": "grep",
        "description": "Search for a regex pattern in a file or files.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The regex pattern to search for."},
                "paths": {
                    "type": "array",
                    "description": "A list of file paths to search in.",
                    "items": {"type": "string"}
                },
                "case_sensitive": {"type": "boolean", "description": "Whether the search is case-sensitive. Defaults to True."}
            },
            "required": ["query", "paths"]
        }
    }

    def run(self, *, query: str, paths: List[str], case_sensitive: bool = True, **kwargs) -> Any:
        results = {}
        flags = 0 if case_sensitive else re.IGNORECASE
        
        try:
            for path_str in paths:
                path = Path(path_str)
                if not path.is_file():
                    results[path_str] = {"error": "Path is not a valid file."}
                    continue

                matches = []
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f, 1):
                        if re.search(query, line, flags):
                            matches.append(f"{i}: {line.strip()}")
                
                if matches:
                    results[path_str] = matches
                else:
                    results[path_str] = "No matches found."
            
            return results
        except Exception as e:
            return {"error": str(e)} 