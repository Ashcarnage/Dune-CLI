# Dune

Dune is an interactive CLI assistant powered by Groq's LLM, specializing in software engineering tasks. It provides an agentic interface that can help you with code analysis, refactoring, debugging, and more through a beautiful rich terminal UI.

## Features

- **Interactive CLI Agent**: Chat with Dune to get help with coding tasks
- **Rich Terminal UI**: Beautiful, colorful interface with gradient headers and formatted output
- **Tool Integration**: Built-in tools for file operations, code search, editing, and more
- **YOLO Mode**: Optional automatic approval mode for faster workflows

## Prerequisites

- Python 3.7+
- A Groq API key ([Get one here](https://console.groq.com/))

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd Dune
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Setup

### Export GROQ API Key

You need to set the `GROQ_API_KEY` environment variable before running Dune. Choose one of the following methods:

#### Option 1: Export in Terminal (Temporary - Current Session Only)

**For macOS/Linux (bash/zsh):**
```bash
export GROQ_API_KEY="your-api-key-here"
```

**For Windows (PowerShell):**
```powershell
$env:GROQ_API_KEY="your-api-key-here"
```

**For Windows (Command Prompt):**
```cmd
set GROQ_API_KEY=your-api-key-here
```

#### Option 2: Add to Shell Profile (Permanent)

**For macOS/Linux (bash):**
```bash
echo 'export GROQ_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**For macOS/Linux (zsh):**
```bash
echo 'export GROQ_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

**For Windows (PowerShell):**
Add to your PowerShell profile:
```powershell
[System.Environment]::SetEnvironmentVariable('GROQ_API_KEY', 'your-api-key-here', 'User')
```

#### Option 3: Create a .env File (Recommended for Development)

Create a `.env` file in the `dune/` directory:
```bash
cd dune
echo "GROQ_API_KEY=your-api-key-here" > .env
```

Note: The current implementation reads from environment variables, so you'll still need to export it or use a tool like `python-dotenv` to load from `.env`.

## Running Dune

### Method 1: Run rich_ui.py directly

```bash
cd dune
python rich_ui.py
```

Or from the project root:
```bash
python -m dune.rich_ui
```

### Method 2: Run with YOLO mode (Auto-approve tool calls)

```bash
cd dune
python rich_ui.py --yolo
```

## Usage

Once Dune is running:

1. Type your question or task in the prompt
2. Dune will analyze your request and use appropriate tools
3. Review tool calls and approve them (unless using `--yolo` mode)
4. Type `exit` to quit

## Example

```
You: Explain the authentication logic in auth.py
Dune: [Analyzes the file and provides explanation]

You: Refactor the code to use async/await
Dune: [Shows plan, executes refactoring with your approval]
```

## Project Structure

```
dune/
├── agent.py          # Core agent logic
├── rich_ui.py        # Main UI entry point
├── groq_client.py    # Groq LLM client
├── gemini_client.py  # Gemini LLM client (alternative)
├── tools/            # Available tools (read_file, write_file, etc.)
└── ...
```

## Troubleshooting

**Error: GROQ_API_KEY environment variable not set**
- Make sure you've exported the API key using one of the methods above
- Verify it's set by running: `echo $GROQ_API_KEY` (macOS/Linux) or `echo $env:GROQ_API_KEY` (Windows PowerShell)

**Module not found errors**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Make sure you're running from the correct directory
