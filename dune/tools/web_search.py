from typing import Any, Dict, Optional
from googlesearch import search
from rich.console import Console

from . import Tool, ToolRegistry

@ToolRegistry.register
class WebSearchTool(Tool):
    """
    Performs a web search using Google and returns the top results.
    """
    name = "web_search"
    description = "Search the web for information on a given query."
    schema: Dict[str, Any] = {
        "name": "web_search",
        "description": "Performs a web search and returns the top results.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query."},
            },
            "required": ["query"],
        }
    }

    def run(self, *, query: str, console: Optional[Console] = None, **kwargs) -> Any:
        if not console:
            console = Console()
        
        console.print(f"Searching the web for: [bold yellow]{query}[/bold yellow]")
        
        try:
            # num_results=5 to keep the output concise for the LLM
            search_results = search(query, num_results=5, advanced=True)
            
            formatted_results = []
            for result in search_results:
                formatted_results.append(
                    f"Title: {result.title}\n"
                    f"Link: {result.url}\n"
                    f"Description: {result.description}\n"
                )
            
            if not formatted_results:
                return {"results": "No results found."}

            return {"results": "\n---\n".join(formatted_results)}

        except Exception as e:
            return {"error": str(e)} 