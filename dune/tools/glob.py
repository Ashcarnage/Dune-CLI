import glob
from typing import Any, Dict, List

from . import Tool, ToolRegistry

@ToolRegistry.register
class GlobTool(Tool):
    """
    Finds files and directories matching a specified pattern.
    """
    name = "glob"
    description = "Find files and directories matching a glob pattern."
    schema: Dict[str, Any] = {
        "name": "glob",
        "description": "Find files and directories matching a glob pattern.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "The glob pattern to match (e.g., 'src/**/*.py')."
                }
            },
            "required": ["pattern"]
        }
    }

    def run(self, *, pattern: str, **kwargs) -> Any:
        try:
            # Using recursive=True to support '**'
            matches = glob.glob(pattern, recursive=True)
            return {"matches": matches}
        except Exception as e:
            return {"error": str(e)} 