import os
import json
from typing import Dict, Any, List, Optional, Generator
from groq import Groq
from dune.tools import ToolRegistry
from rich.console import Console

# --- Groq LLM Endpoint ---
# This is an alternative to the Gemini endpoint, using the Groq API.
# It requires the GROQ_API_KEY environment variable to be set.
class GroqLLMEndpoint:
    """A service layer for interacting with the Groq API."""

    def __init__(self, api_key: str, model: str = "qwen/qwen3-32b", console: Console = None):
        self._api_key = api_key
        self._model = model
        self._client = Groq(api_key=self._api_key)
        self.console = console or Console()

    def generate(
        self,
        history: List[Dict],
        *,
        tools: Optional[List[Dict]] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a response from the Groq API."""
        
        messages = self._prepare_messages(history, system_prompt)
        
        try:
            params = {
                "messages": messages,
                "model": self._model,
            }
            if tools:
                # The Groq API expects tools in a specific format.
                # Our agent passes them in a Gemini-like format, so we need to adapt.
                gemini_functions = tools[0].get('function_declarations', [])
                
                # Each tool needs to be wrapped with "type": "function"
                groq_tools = [{"type": "function", "function": func} for func in gemini_functions]
                
                params["tools"] = groq_tools
                params["tool_choice"] = "auto"

            chat_completion = self._client.chat.completions.create(**params)
            
            response_message = chat_completion.choices[0].message
            
            # Check for tool calls
            if response_message.tool_calls:
                tool_call = response_message.tool_calls[0]
                return {
                    "function_call": {
                        "name": tool_call.function.name,
                        "args": json.loads(tool_call.function.arguments)
                    }
                }

            return {"text": response_message.content}

        except Exception as e:
            print(f"Groq API Error: {e}")
            return {"error": str(e)}

    def generate_stream(self, messages: list[dict[str, any]], tools: list[dict[str, any]]) -> Generator[str, None, None]:
        """Generates a response from the Groq API, streaming the output."""
        try:
            stream = self._client.chat.completions.create(
                messages=messages,
                model=self._model,
                tools=tools,
                tool_choice="auto",
                stream=True,
            )
            for chunk in stream:
                yield chunk
        except Exception as e:
            self.console.print(f"An unexpected error occurred during streaming: {e}", style="bold red")

    def _prepare_messages(self, history: List[Dict], system_prompt: Optional[str]) -> List[Dict]:
        """Converts our internal history format to the Groq/OpenAI format."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        for turn in history:
            role = turn["role"]
            if role == "user":
                messages.append({"role": "user", "content": turn["content"]})
            elif role == "assistant":
                # Assistant messages can have content, tool_calls, or both
                message = {"role": "assistant", "content": turn.get("content")}
                if "tool_calls" in turn:
                    message["tool_calls"] = turn["tool_calls"]
                messages.append(message)
            elif role == "tool":
                messages.append({
                    "role": "tool",
                    "tool_call_id": turn["tool_call_id"],
                    "content": turn["content"],
                })

        # Filter out any messages with None content that are not tool calls
        messages = [
            m for m in messages if m.get("content") is not None or m.get("tool_calls") is not None
        ]
        return messages

    def get_tool_schemas(self) -> list[dict[str, any]]:
        """Returns a list of tool schemas for the Groq API."""
        tool_classes = ToolRegistry.list_tools()
        schemas = []
        for tool_cls in tool_classes:
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool_cls.name,
                    "description": tool_cls.description,
                    "parameters": tool_cls.schema,
                }
            })
        return schemas 