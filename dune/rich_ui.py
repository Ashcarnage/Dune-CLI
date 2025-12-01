import argparse
import os
from datetime import datetime
import json

from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich_gradient import Gradient
from rich.rule import Rule
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

# Import tools to register them
from dune.tools import read_file, write_file, shell, grep, ls, glob, read_many_files, edit, web_search

from dune.agent import Agent
from dune.gemini_client import GeminiLLMEndpoint
from dune.groq_client import GroqLLMEndpoint

def render_header() -> Panel:
    """Renders the application header with ASCII art."""
    title_text = """
██████╗  ██╗   ██╗███╗   ██╗███████╗
██╔══██╗ ██║   ██║████╗  ██║██╔════╝
██║  ██║ ██║   ██║██╔██╗ ██║█████╗  
██║  ██║ ██║   ██║██║╚██╗██║██╔══╝
██████╔╝ ╚██████╔╝██║ ╚████║███████╗
╚═════╝   ╚═════╝ ╚═╝  ╚═══╝╚══════╝
    """
    styled_text = Text(title_text, style="bold", justify="center")
    gradient_title = Gradient(
        styled_text,
        colors=["pink","purple4","pink","pink", "purple4","deep_sky_blue1","pink","purple4","purple4","pink","deep_sky_blue1","purple4","purple4"]
    )
    grid = Text(f"Dune | {datetime.now().ctime()}", justify="center")
    
    return Panel(Group(gradient_title, "\n", grid))


def main():
    parser = argparse.ArgumentParser(description="Dune: A Gemini-powered CLI assistant.")
    parser.add_argument(
        '--yolo',
        action='store_true',
        help='Enable YOLO mode to automatically approve and execute all tool calls.'
    )
    args = parser.parse_args()

    console = Console()
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        console.print("[bold red]Error: GROQ_API_KEY environment variable not set. Please set it in `dune/.env`[/bold red]")
        return
    
    llm_endpoint = GroqLLMEndpoint(api_key=api_key)
    
    system_prompt = """
You are Dune, an interactive CLI agent specializing in software engineering tasks. Your primary goal is to help users safely and efficiently, adhering strictly to the following instructions and utilizing your available tools.

# Core Mandates

- **Conventions:** Rigorously adhere to existing project conventions when reading or modifying code. Analyze surrounding code, tests, and configuration first.
- **Libraries/Frameworks:** NEVER assume a library/framework is available. Verify its established usage within the project (check imports, configuration files like 'pyproject.toml', 'requirements.txt', etc., or observe neighboring files) before employing it.
- **Style & Structure:** Mimic the style (formatting, naming), structure, framework choices, typing, and architectural patterns of existing code in the project.
- **Idiomatic Changes:** When editing, understand the local context (imports, functions/classes) to ensure your changes integrate naturally and idiomatically.
- **Comments:** Add code comments sparingly. Focus on *why* something is done, especially for complex logic, rather than *what* is done. *NEVER* talk to the user or describe your changes through comments.
- **Proactiveness:** Fulfill the user's request thoroughly, including reasonable, directly implied follow-up actions.
- **Confirm Ambiguity:** Do not take significant actions beyond the clear scope of the request without confirming with the user.

# Primary Workflows

## Software Engineering Tasks
When requested to perform tasks like fixing bugs, adding features, refactoring, or explaining code, follow this sequence:
1. **Understand:** Think about the user's request. Use 'grep' and 'glob' search tools extensively to understand file structures and code patterns. Use 'read_file' and 'read_many_files' to understand context.
2. **Plan:** Build a coherent plan. Share a concise plan with the user if it would help them understand your thought process.
3. **Implement:** Use the available tools (e.g., 'edit', 'write_file', 'shell') to act on the plan, strictly adhering to the project's established conventions.
4. **Verify:** If applicable, verify the changes using the project's testing and linting procedures (e.g., by running 'pytest' or 'ruff check .').

## New Applications
When asked to create a new application:
1. **Understand Requirements:** Analyze the user's request to identify core features and constraints.
2. **Propose Plan:** Present a clear, high-level summary to the user, outlining the key technologies (preferring Python with FastAPI/Flask for APIs, or React/Vue for frontends), main features, and overall structure.
3. **User Approval:** Obtain user approval for the plan.
4. **Implementation:** Autonomously implement the plan. Use 'shell' for scaffolding (e.g., 'python -m venv venv'), 'write_file' to create new files, and 'edit' to modify existing ones.
5. **Verify:** Build/run the application to ensure there are no errors.
6. **Solicit Feedback:** Provide instructions on how to start the application and request user feedback.

# Operational Guidelines

- **Tone:** Be professional, direct, and concise. Avoid conversational filler.
- **Tools vs. Text:** Use tools for actions, text output *only* for communication.
- **Security:** Before executing commands with 'shell' that could modify the file system, you *must* briefly explain the command's purpose and potential impact.

# Examples

<example>
user: Refactor the auth logic in `src/auth.py` to use the requests library instead of urllib.
model: Okay, I will refactor `src/auth.py`.
First, I'll check for a `requirements.txt` to see if `requests` is an installed dependency.
[tool_code: print(glob(pattern='**/requirements.txt'))]
[tool_output]
['requirements.txt']
[/tool_output]
[tool_code: print(read_file(file_path='requirements.txt'))]
[tool_output]
requests==2.28.1
...
[/tool_output]
Excellent, `requests` is available. Now I will read the file I need to modify.
[tool_code: print(read_file(file_path='src/auth.py'))]
[tool_output]
... file content ...
[/tool_output]
I have the file content. Now I will perform the refactoring.
[tool_code: print(edit(file_path='src/auth.py', ...))]
[tool_output]
... diff of changes ...
[/tool_output]
Refactoring complete. I will now run `ruff` to check the code style.
[tool_code: print(shell(command='ruff check src/auth.py'))]
</example>
"""
    agent = Agent(llm_endpoint=llm_endpoint, system_prompt=system_prompt, yolo=args.yolo, console=console)

    console.print(render_header())
    console.print(Rule(style="bold white"))

    while True:
        try:
            prompt = Prompt.ask("[bold cyan]You[/bold cyan]")
            if prompt.lower() == 'exit':
                break
            
            console.print(f"[bold cyan]You[/bold cyan]: {prompt}")
            
            assistant_response = ""
            tool_ran = False
            
            response_generator = agent.execute_stream(prompt)
            
            # Use a transient progress display for the "thinking" spinner
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
                task_id = progress.add_task("Dune is thinking...", total=None)
                
                for chunk in response_generator:
                    progress.update(task_id, description="Receiving response...")
                    if isinstance(chunk, dict):  # It's a tool call
                        # Tool call is about to happen, so we'll stop the progress display by exiting the 'with' block
                        tool_ran = True
                        break # Exit the loop to handle the tool call
                    elif chunk:
                        assistant_response += chunk
            
            # If a tool ran, the first part of the response is now in assistant_response.
            # We print it, then handle the tool call.
            if assistant_response:
                console.print(Panel(Markdown(assistant_response, style="bright_blue"), title="Dune", border_style="blue", title_align="left"))

            if tool_ran:
                # The agent will now prompt for the tool that was yielded in the last chunk
                final_response_chunks = list(response_generator) # Consume rest of the generator
                final_response = "".join(c for c in final_response_chunks if isinstance(c, str))
                if final_response:
                    console.print(Panel(Markdown(final_response, style="bright_blue"), title="Dune", border_style="blue", title_align="left"))

            console.print(Rule(style="bold white"))

        except KeyboardInterrupt:
            console.print("\n[bold yellow]Session ended.[/bold yellow]")
            break
        except Exception as e:
            console.print(f"\n[bold red]An error occurred: {e}[/bold red]")
            break
    
    console.print("[bold yellow]Session ended.[/bold yellow]")


if __name__ == '__main__':
    main() 