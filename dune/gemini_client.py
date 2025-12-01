import time
import json
from typing import Optional, Dict, Any, List
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import requests

from .auth import CodeAssistOAuth
from . import converter

# Constants from gemini-cli source
CODE_ASSIST_ENDPOINT = 'https://cloudcode-pa.googleapis.com'
CODE_ASSIST_API_VERSION = 'v1internal'
USER_AGENT = 'GeminiCLI/20.18.1 (darwin; arm64)'

# Cache paths
CREDENTIALS_DIR = Path.home() / '.config' / 'mycli'
PROJECT_ID_CACHE_PATH = CREDENTIALS_DIR / 'project_id.json'

class GeminiClient:
    _instance: Optional['GeminiClient'] = None
    _initialized: bool = False

    def __init__(self, credentials: Credentials, project_id: str):
        self._credentials = credentials
        self._project_id = project_id

    @property
    def project_id(self) -> str:
        """Get the project ID."""
        return self._project_id

    @classmethod
    def create(cls) -> "GeminiClient":
        """Create or return the singleton GeminiClient instance."""
        if cls._instance is not None and cls._initialized:
            # Ensure credentials are still valid
            if not cls._instance._credentials.valid:
                if cls._instance._credentials.refresh_token:
                    cls._instance._credentials.refresh(Request())
                else:
                    # Need to re-authenticate, clear instance
                    cls._instance = None
                    cls._initialized = False
            else:
                return cls._instance

        if cls._instance is None or not cls._initialized:
            oauth = CodeAssistOAuth()
            credentials = oauth.get_auth_client()
            
            # Try to load cached project_id first
            project_id = cls._load_cached_project_id()
            
            if not project_id:
                # Perform the onboarding flow to get the project_id
                project_id = cls._perform_onboarding(credentials)
                # Cache the project_id
                cls._save_project_id(project_id)
            else:
                print("Using cached project ID, skipping onboarding...")
            
            cls._instance = cls(credentials, project_id)
            cls._initialized = True
        
        return cls._instance

    @staticmethod
    def _load_cached_project_id() -> Optional[str]:
        """Load cached project ID from file."""
        try:
            if PROJECT_ID_CACHE_PATH.exists():
                with open(PROJECT_ID_CACHE_PATH, 'r') as f:
                    data = json.load(f)
                    return data.get('project_id')
        except (json.JSONDecodeError, FileNotFoundError, KeyError):
            pass
        return None

    @staticmethod
    def _save_project_id(project_id: str):
        """Save project ID to cache file."""
        try:
            CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
            with open(PROJECT_ID_CACHE_PATH, 'w') as f:
                json.dump({'project_id': project_id}, f)
        except Exception as e:
            print(f"Warning: Failed to cache project ID: {e}")

    @staticmethod
    def _perform_onboarding(credentials: Credentials) -> str:
        print("Performing one-time onboarding with Google...")
        
        # Step 1: loadCodeAssist
        client_metadata = {
            'ideType': 'IDE_UNSPECIFIED',
            'platform': 'PLATFORM_UNSPECIFIED',
            'pluginType': 'GEMINI',
        }
        
        load_req_body = {
            'metadata': client_metadata,
        }
        
        load_res_data = GeminiClient._api_request(
            'loadCodeAssist', 
            credentials, 
            load_req_body
        )

        # Step 2: onboardUser
        onboard_tier_id = 'legacy-tier'
        if 'allowedTiers' in load_res_data:
            default_tier = next((t for t in load_res_data['allowedTiers'] if t.get('isDefault')), None)
            if default_tier:
                onboard_tier_id = default_tier['id']
        
        cloudaicompanion_project = load_res_data.get('cloudaicompanionProject')
        
        onboard_req_body = {
            'tierId': onboard_tier_id,
            'cloudaicompanionProject': cloudaicompanion_project,
            'metadata': client_metadata,
        }

        # Poll onboardUser until the long-running operation is done
        while True:
            print("Polling onboardUser status...")
            lro_res_data = GeminiClient._api_request(
                'onboardUser', 
                credentials, 
                onboard_req_body
            )

            if lro_res_data.get('done', False):
                project_id = lro_res_data.get('response', {}).get('cloudaicompanionProject', {}).get('id')
                if not project_id:
                    raise Exception("Failed to get project_id from onboarding response.")
                print("Onboarding successful!")
                return project_id
            
            time.sleep(5)

    def _make_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a request to the Gemini API with the provided request data."""
        response_data = self._api_request('generateContent', self._credentials, request_data)
        
        # Return the full response for web tools to process
        return response_data.get('response', {})
    
    def chat(self, prompt: str) -> str:
        """Simple chat method for backward compatibility."""
        return self.generate_content([{"role": "user", "parts": [{"text": prompt}]}])

    def generate_content(self, history: List[Dict], tools: Optional[List[Dict]] = None, system_prompt: Optional[str] = None) -> str:
        # Create the request using the exact same structure as the TypeScript converter
        req_body = converter.to_generate_content_request(
            model="gemini-2.5-pro",
            contents=history,
            system_instruction=system_prompt,
            tools=tools,
        )
        req_body['project'] = self._project_id
        
        response_data = self._api_request('generateContent', self._credentials, req_body)
        
        try:
            # Check for a function call first
            part = response_data['response']['candidates'][0]['content']['parts'][0]
            function_call = part.get('functionCall')
            if function_call:
                return {"function_call": function_call}

            # Fallback to text response
            return {"text": part['text']}
        except (KeyError, IndexError) as e:
            raise Exception(f"Failed to parse response from Gemini: {response_data}") from e

    @staticmethod
    def _api_request(method: str, credentials: Credentials, json_body: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure token is fresh
        if not credentials.valid:
            credentials.refresh(Request())

        headers = {
            'Authorization': f'Bearer {credentials.token}',
            'Content-Type': 'application/json',
            'User-Agent': USER_AGENT,
        }
        
        url = f'{CODE_ASSIST_ENDPOINT}/{CODE_ASSIST_API_VERSION}:{method}'
        
        try:
            # Log the request for debugging
            print("--- API Request ---")
            print(f"URL: {url}")
            print(f"Payload: {json.dumps(json_body, indent=2)}")
            print("-------------------")

            response = requests.post(url, headers=headers, json=json_body)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Request Error: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response Status: {e.response.status_code}")
                print(f"Response Body: {e.response.text}")
            raise

    @classmethod
    def clear_cache(cls):
        """Clear cached instance and project ID (for testing or re-authentication)."""
        cls._instance = None
        cls._initialized = False
        try:
            if PROJECT_ID_CACHE_PATH.exists():
                PROJECT_ID_CACHE_PATH.unlink()
                print("Cleared project ID cache.")
        except Exception as e:
            print(f"Warning: Failed to clear project ID cache: {e}")

# -----------------------
# Public-facing LLM Endpoint
# -----------------------
class GeminiLLMEndpoint:
    """A thin wrapper around the singleton GeminiClient exposing a clean LLM API."""

    @staticmethod
    def generate(
        history: List[Dict],
        *,
        tools: Optional[List[Dict]] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a response from Gemini.

        Args:
            history: The full conversation history.
            tools: Optional tool definitions for function calling.
            system_prompt: Optional system instruction.

        Returns:
            A dictionary with either:
              {"text": str} or {"function_call": {...}}
        """
        client = GeminiClient.create()
        return client.generate_content(history, tools=tools, system_prompt=system_prompt)

if __name__ == '__main__':
    # A simple test to verify the full flow
    print("Attempting to create GeminiClient...")
    client = GeminiClient.create()
    print(f"Client created successfully with Project ID: {client._project_id}")
    
    print("\nSending a test prompt...")
    response = client.generate_content("What is the capital of France?")
    print(f"\nGemini Response: {response}")
    print("\nCreating another client instance (should reuse existing)...")
    client2 = GeminiClient.create()
    print(f"Second client instance has same Project ID: {client2._project_id}")
    print(f"Same instance: {client is client2}")

