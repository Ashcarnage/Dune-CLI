import subprocess
from typing import Any, Dict, Optional
from rich.console import Console
from rich.prompt import Prompt

from . import Tool, ToolRegistry

@ToolRegistry.register
class ShellTool(Tool):
    """Execute a shell command in the workspace root."""

    name = "shell"
    description = "Execute a shell command."
    schema: Dict[str, Any] = {
        "name": "shell",
        "description": "Execute a shell command.",
        "parameters": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"]
        }
    }

    def run(self, *, command: str, yolo: bool = False, console: Optional[Console] = None, **kwargs) -> Any:
        if not console:
            console = Console()
        
        if not yolo:
            console.print(f"Shell command: [bold yellow]{command}[/bold yellow]")
            if Prompt.ask("Approve this command?", choices=["y", "n"], default="n") != "y":
                return {"error": "User rejected the shell command."}

        try:
            process = subprocess.run(
                command,
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            return {"stdout": process.stdout, "stderr": process.stderr}
        except subprocess.CalledProcessError as e:
            return {"error": f"Command failed with exit code {e.returncode}", "stdout": e.stdout, "stderr": e.stderr}
        except Exception as e:
            return {"error": str(e)} 