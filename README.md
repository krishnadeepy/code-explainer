# Code-Exapliner

1. Clone this repository

2. Install dependencies: 
   ```bash
   pip install -r requirements.txt
   ```

3. Set up LLM in [`utils/call_llm.py`](./utils/call_llm.py) by providing credentials (API key or project name). We highly recommend the latest models with thinking capabilities (Gemini Pro 2.5, Claude 3.7 with thinking, O1). You can verify if it is correctly set up by running:
   ```bash
   python utils/call_llm.py
   ```

4. Generate a complete codebase tutorial by running the main script:
    ```bash
    python main.py https://github.com/username/repo --include "*.py" "*.js" --exclude "tests/*" --max-size 50000
    ```
    - `repo_url` - URL of the GitHub repository (required)
    - `-n, --name` - Project name (optional, derived from URL if omitted)
    - `-t, --token` - GitHub token (or set GITHUB_TOKEN environment variable)
    - `-o, --output` - Output directory (default: ./output)
    - `-i, --include` - Files to include (e.g., "*.py" "*.js")
    - `-e, --exclude` - Files to exclude (e.g., "tests/*" "docs/*")
    - `-s, --max-size` - Maximum file size in bytes (default: 100KB)
      
The application will crawl the repository, analyze the codebase structure, generate tutorial content, and save the output in the specified directory (default: ./output).
