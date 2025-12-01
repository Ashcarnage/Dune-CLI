import argparse
import os
from rich.console import Console
from rich.panel import Panel

# Import tools to register them
from dune.tools import read_file, write_file, shell, grep, ls, glob, read_many_files, edit, web_search

from dune.agent import Agent
from dune.gemini_client import GeminiLLMEndpoint
from dune.groq_client import GroqLLMEndpoint


def main():
    console = Console()
    console.print("[bold purple]Welcome to Dune ✨[/bold purple]")

    parser = argparse.ArgumentParser(description="Dune: A Gemini-powered CLI assistant.")
    parser.add_argument('--prompt', type=str, help="The prompt to run.")
    parser.add_argument('--clear-cache', action='store_true', help="Clear the authentication cache.")
    parser.add_argument('--llm', type=str, default='groq', choices=['gemini', 'groq'], help="The LLM to use.")
    parser.add_argument(
        '--yolo',
        action='store_true',
        help='Enable YOLO mode to automatically approve and execute all tool calls.'
    )
    args = parser.parse_args()

    if args.clear_cache:
        from dune.gemini_client import GeminiClient
        GeminiClient.clear_cache()
        console.print("[bold yellow]Cleared cached credentials and project ID.[/bold yellow]")
        return

    # Select and initialize the LLM endpoint
    if args.llm == 'groq':
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            console.print("[bold red]Error: GROQ_API_KEY environment variable not set.[/bold red]")
            return
        llm_endpoint = GroqLLMEndpoint(api_key=api_key)
        console.print(Panel("Using Groq LLM endpoint.", title="[bold green]System[/bold green]", border_style="green"))
    else:
        # Default to Gemini, which is better for tool calling
        llm_endpoint = GeminiLLMEndpoint()
        console.print(Panel("Using Gemini LLM endpoint.", title="[bold green]System[/bold green]", border_style="green"))

    # Initialize the agent
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
    console.print(Panel("Agent initialized. Type 'exit' to quit.", title="[bold green]System[/bold green]", border_style="green"))

    if args.prompt:
        response = agent.execute(args.prompt)
        console.print(Panel(response, title="[bold blue]Dune[/bold blue]", border_style="blue"))
        return

    # Interactive mode
    while True:
        try:
            user_input = console.input("[bold cyan]You[/bold cyan]: ")
            if user_input.lower() == 'exit':
                break

            console.print("[bold cyan]Dune[/bold cyan]: ", end="")
            response_generator = agent.execute_stream(user_input)
            for chunk in response_generator:
                console.print(chunk, end="", style="bright_blue")
            console.print()  # For a new line after the response

        except KeyboardInterrupt:
            console.print("\nExiting...", style="bold red")
            break
        except Exception as e:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
    
    console.print("[bold yellow]Session ended.[/bold yellow]")


if __name__ == '__main__':
    main()
