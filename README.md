# RAG_MCP
A RAG-ready MCP server for semantic PDF search with OCR, FAISS, and transformers—plug into any MCP client and retrieve intelligent answers within your MCP client.

<br>

## Step 1: Create virtual env and install requirements
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv init rag_mcp
cd rag_mcp
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
brew install tesseract
```

## Step 2: Add config to your MCP client
```bash
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
...
{
    "mcpServers": {
        "rag": {
            "command": "/Users/XXX/.local/bin/uv",
            "args": [
                "--directory",
                "/Users/XXX/Documents/RAG_MCP",
                "run",
                "rag.py"
            ]
        }
    }
}
```

## Step 5: Make MCP server executable
```bash
chmod +x rag.py
```

## Step 6: Run MCP server
```bash
uv run rag.py
```

## Step 7: Run MCP client and query
```bash
Parse the pdfs and tell me about 18 Church St. and what significance it has.
```

<br>

## License
[Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0)
