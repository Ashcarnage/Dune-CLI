from typing import Any, Dict, Optional
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt

from . import Tool, ToolRegistry

@ToolRegistry.register
class EditTool(Tool):
    """
    Performs a search-and-replace on a file.
    """
    name = "edit"
    description = (
        "Replaces text within a file. This tool requires providing significant context "
        "around the change to ensure precise targeting. Always use the `read_file` tool "
        "to examine the file's current content before attempting a text replacement."
    )
    schema: Dict[str, Any] = {
        "name": "edit",
        "description": "Search for a specific piece of text in a file and replace it.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The path to the file to edit."},
                "search_text": {
                    "type": "string",
                    "description": (
                        "The exact literal text to replace, including several lines of context "
                        "before and after the target text. Must match whitespace and indentation precisely."
                    )
                },
                "replace_text": {
                    "type": "string",
                    "description": "The exact literal text to replace `search_text` with."
                }
            },
            "required": ["path", "search_text", "replace_text"]
        }
    }

    def run(self, *, path: str, search_text: str, replace_text: str, yolo: bool = False, console: Optional[Console] = None, **kwargs) -> Any:
        file_path = Path(path)
        if not console:
            console = Console()

        if not file_path.is_file():
            return {"error": f"File not found at {path}"}

        try:
            original_content = file_path.read_text()
            if search_text not in original_content:
                return {"error": f"Search text not found in file. Use `read_file` to see the exact content."}
            
            # Count occurrences to inform the user
            occurrences = original_content.count(search_text)

            if not yolo:
                console.print(f"Found {occurrences} occurrence(s) of the search text.")
                console.print(f"About to replace '[bold red]{search_text}[/bold red]' with '[bold green]{replace_text}[/bold green]' in {path}.")
                if Prompt.ask("Approve this change?", choices=["y", "n"], default="n") != "y":
                    return {"error": "User rejected the edit."}

            # For simplicity, we'll replace only the first occurrence, which is safer.
            new_content = original_content.replace(search_text, replace_text, 1)
            file_path.write_text(new_content)
            
            return {"success": True, "path": str(file_path)}

        except Exception as e:
            return {"error": str(e)} 