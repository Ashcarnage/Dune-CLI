from typing import Dict, Any, List, Optional
import json
from rich.console import Console
from rich.prompt import Prompt
import difflib
from pathlib import Path

from .tools import ToolRegistry

DANGEROUS_TOOLS = ["shell", "write_file", "edit"]

# The Agent will now accept any object that has a `generate` method
# This makes it compatible with both GeminiLLMEndpoint and GroqLLMEndpoint
class Agent:
    def __init__(self, llm_endpoint: Any, system_prompt: Optional[str] = None, yolo: bool = False, console: Optional[Console] = None):
        self._llm = llm_endpoint
        self._history = []
        self._system_prompt = system_prompt
        self._yolo = yolo
        self.console = console or Console()
        # The tools are registered automatically when they are imported.
        # We need to make sure they are imported somewhere. cli.py is a good place.

    def _get_tool_definitions(self) -> List[Dict]:
        """Gets the JSON schema for all registered tools."""
        tool_schemas = [tool.schema for tool in ToolRegistry.list_tools()]
        return [{"function_declarations": tool_schemas}]

    def execute(self, prompt: str, max_turns: int = 25) -> str:
        """Executes a prompt, handling a multi-step reasoning loop."""
        self._history.append({"role": "user", "parts": [{"text": prompt}]})
        
        for _ in range(max_turns):
            tools = self._get_tool_definitions()
            
            with self.console.status("[bold green]Agent is thinking...[/bold green]"):
                llm_response = self._llm.generate(
                    self._history,
                    tools=tools,
                    system_prompt=self._system_prompt
                )

            if "function_call" in llm_response:
                self._history.append({"role": "model", "parts": [llm_response]})
                
                function_call = llm_response["function_call"]
                tool_name = function_call["name"]
                tool_args = function_call.get("args", {})

                # Approval check for dangerous tools
                if tool_name in DANGEROUS_TOOLS and not self._yolo:
                    # Special handling for the 'edit' tool to show a diff
                    if tool_name == 'edit':
                        try:
                            path = tool_args.get('path')
                            new_content = tool_args.get('new_content', '')
                            original_content = Path(path).read_text()
                            
                            diff = difflib.unified_diff(
                                original_content.splitlines(keepends=True),
                                new_content.splitlines(keepends=True),
                                fromfile=f"a/{path}",
                                tofile=f"b/{path}",
                            )
                            self.console.print("--- DIFF ---")
                            self.console.print("".join(diff))
                            self.console.print("------------")
                        except Exception as e:
                            self.console.print(f"[bold red]Could not generate diff: {e}[/bold red]")

                    self.console.print(f"Tool call: [bold yellow]{tool_name}[/bold yellow] with args: [bold yellow]{tool_args}[/bold yellow]")
                    if Prompt.ask("Approve this tool call?", choices=["y", "n"], default="n") != "y":
                        tool_result = {"error": f"Tool call for '{tool_name}' was rejected by the user."}
                    else:
                        self.console.print(f"Executing tool: {tool_name}...")
                        tool_result = ToolRegistry.run(tool_name, **tool_args)
                else:
                    self.console.print(f"Executing tool: {tool_name} with args: {tool_args}")
                    tool_result = ToolRegistry.run(tool_name, **tool_args)

                self._history.append({
                    "role": "function",
                    "parts": [{"functionResponse": {"name": tool_name, "response": tool_result}}]
                })
                # Continue the loop to let the LLM process the tool result
                continue
            
            elif "text" in llm_response:
                final_response = llm_response["text"]
                self._history.append({"role": "model", "parts": [{"text": final_response}]})
                return final_response
            
            else:
                return f"Error: Invalid response from LLM: {llm_response}"

        return "Error: Agent exceeded maximum turns."

    def execute_stream(self, prompt: str, max_turns: int = 10):
        """
        Executes a prompt and streams the output, handling multiple reasoning turns.
        Yields text chunks for direct output, and tool call dictionaries for UI feedback.
        """
        self._history.append({"role": "user", "content": prompt})

        for _ in range(max_turns):
            messages = self._llm._prepare_messages(self._history, self._system_prompt)
            tool_schemas = self._llm.get_tool_schemas()

            # Get response from the LLM
            stream = self._llm.generate_stream(messages=messages, tools=tool_schemas)

            # Process the stream
            full_response_content = ""
            tool_calls = []
            current_tool_call_index = 0
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content
                    full_response_content += delta.content

                if delta.tool_calls:
                    for tc_chunk in delta.tool_calls:
                        # A new tool call is starting
                        if len(tool_calls) <= tc_chunk.index:
                            tool_calls.append({
                                "id": tc_chunk.id,
                                "type": "function",
                                "function": {"name": tc_chunk.function.name, "arguments": ""}
                            })
                        # Append the arguments to the current tool call
                        if tc_chunk.function and tc_chunk.function.arguments:
                             tool_calls[tc_chunk.index]["function"]["arguments"] += tc_chunk.function.arguments

            # After the stream, decide what to do
            if tool_calls:
                # A tool needs to be called
                assistant_message = {"role": "assistant", "content": full_response_content or "", "tool_calls": tool_calls}
                self._history.append(assistant_message)

                tool_outputs = []
                for tool_call in tool_calls:
                    tool_name = tool_call["function"]["name"]
                    try:
                        tool_args = json.loads(tool_call["function"]["arguments"])
                        yield {"name": tool_name, "args": tool_args} # Yield for UI
                    except json.JSONDecodeError:
                        error_msg = f"Error: Invalid JSON arguments for tool {tool_name}: {tool_call['function']['arguments']}"
                        yield error_msg
                        tool_outputs.append({"role": "tool", "tool_call_id": tool_call["id"], "name": tool_name, "content": error_msg})
                        continue

                    # Execute the tool
                    tool_output_content = self._execute_tool(tool_name, tool_args)
                    tool_outputs.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": tool_name,
                        "content": json.dumps(tool_output_content), # Ensure content is JSON string
                    })
                
                self._history.extend(tool_outputs)
                continue # Go to the next turn in the reasoning loop

            else:
                # No tool call, this is a final text response
                self._history.append({"role": "assistant", "content": full_response_content})
                return # End of conversation turn

    def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]):
        """Executes a single tool and returns its output."""
        if tool_name in DANGEROUS_TOOLS and not self._yolo:
            self.console.print(f"Tool call: [bold yellow]{tool_name}[/bold yellow] with args: [bold yellow]{tool_args}[/bold yellow]")
            if Prompt.ask("Approve this tool call?", choices=["y", "n"], default="n") != "y":
                return {"error": f"Tool call for '{tool_name}' was rejected by the user."}
        
        try:
            # The ToolRegistry's run method returns the direct output of the tool function
            return ToolRegistry.run(tool_name, **tool_args)
        except Exception as e:
            return {"error": f"Error executing tool {tool_name}: {e}"}

    def _process_response(self, response: Dict[str, Any]):
        if response is None:
            return "Error: Invalid response from LLM"
        return response
