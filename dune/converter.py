"""
This module is a Python port of the converter.ts file from the Gemini CLI source.
It is responsible for converting the high-level request parameters into the specific
JSON structure expected by the Code Assist API.
"""
from typing import Dict, Any, List, Optional, Union

def to_generate_content_request(
    model: str,
    contents: List[Dict],
    system_instruction: Optional[str] = None,
    tools: Optional[List[Dict]] = None,
    tool_config: Optional[Dict] = None,
    # Add other parameters from VertexGenerateContentRequest as needed
) -> Dict[str, Any]:
    """Converts parameters to the `generateContent` request body format."""
    
    request = {
        "contents": contents,
    }

    if system_instruction:
        # The API expects system_instruction as a Content object
        request["systemInstruction"] = {
            "role": "system", 
            "parts": [{"text": system_instruction}]
        }

    if tools:
        request["tools"] = tools

    if tool_config:
        request["toolConfig"] = tool_config

    # The final request body is nested under a top-level object
    return {
        "model": model,
        "request": request
    }

def to_contents(contents: Union[str, List[Dict], Dict]) -> List[Dict]:
    """Ensures contents are in the correct list format."""
    if isinstance(contents, str):
        return [{"role": "user", "parts": [{"text": contents}]}]
    if isinstance(contents, dict):
        return [contents]
    return contents 