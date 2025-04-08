import requests
import base64
import os
import time
import fnmatch
from typing import Union, Set, List, Dict, Tuple, Any
from urllib.parse import urlparse

def crawl_github_files(
    repo_url, 
    token=None, 
    max_file_size: int = 1 * 1024 * 1024,  # 1 MB
    use_relative_paths: bool = False,
    include_patterns: Union[str, Set[str]] = None,
    exclude_patterns: Union[str, Set[str]] = None
):
    """
    Crawl files from a specific path in a GitHub repository at a specific commit.
    
    Args:
        repo_url (str): URL of the GitHub repository with specific path and commit
                        (e.g., 'https://github.com/microsoft/autogen/tree/e45a15766746d95f8cfaaa705b0371267bec812e/python/packages/autogen-core/src/autogen_core')
        token (str, optional): GitHub personal access token. Required for private repositories and recommended for public repos to avoid rate limits.
        max_file_size (int, optional): Maximum file size in bytes to download (default: 1 MB)
        use_relative_paths (bool, optional): If True, file paths will be relative to the specified subdirectory
        include_patterns (str or set of str, optional): Pattern or set of patterns specifying which files to include (e.g., "*.py", {"*.md", "*.txt"}).
                                                       If None, all files are included.
        exclude_patterns (str or set of str, optional): Pattern or set of patterns specifying which files to exclude.
                                                       If None, no files are excluded.
    
    Returns:
        dict: Dictionary with files and statistics
    """
    # Convert single pattern to set
    if include_patterns and isinstance(include_patterns, str):
        include_patterns = {include_patterns}
    if exclude_patterns and isinstance(exclude_patterns, str):
        exclude_patterns = {exclude_patterns}
    
    # Parse GitHub URL to extract owner, repo, commit/branch, and path
    parsed_url = urlparse(repo_url)
    path_parts = parsed_url.path.strip('/').split('/')
    
    if len(path_parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {repo_url}")
    
    # Extract the basic components
    owner = path_parts[0]
    repo = path_parts[1]
    
    # Check if URL contains a specific branch/commit
    if 'tree' in path_parts:
        tree_index = path_parts.index('tree')
        ref = path_parts[tree_index + 1]
        # Combine all parts after the ref as the path
        path_start = tree_index + 2
        specific_path = '/'.join(path_parts[path_start:]) if path_start < len(path_parts) else ""
    else:
        ref = "main"  # Default branch
        specific_path = ""
    
    # Setup for GitHub API
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    
    # Dictionary to store path -> content mapping
    files = {}
    skipped_files = []
    
    def should_include_file(file_path: str, file_name: str) -> bool:
        """Determine if a file should be included based on patterns"""
        # If no include patterns are specified, include all files
        if not include_patterns:
            include_file = True
        else:
            # Check if file matches any include pattern
            include_file = any(fnmatch.fnmatch(file_name, pattern) for pattern in include_patterns)
        
        # If exclude patterns are specified, check if file should be excluded
        if exclude_patterns and include_file:
            # Exclude if file matches any exclude pattern
            exclude_file = any(fnmatch.fnmatch(file_path, pattern) for pattern in exclude_patterns)
            return not exclude_file
        
        return include_file
    
    def fetch_contents(path):
        """Fetch contents of the repository at a specific path and commit"""
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": ref}
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 403 and 'rate limit exceeded' in response.text.lower():
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            wait_time = max(reset_time - time.time(), 0) + 1
            print(f"Rate limit exceeded. Waiting for {wait_time:.0f} seconds...")
            time.sleep(wait_time)
            return fetch_contents(path)
            
        if response.status_code == 404:
            if not token:
                print(f"Error 404: Repository not found or is private. If this is a private repository, you need to provide a token.")
            else:
                print(f"Error 404: Path '{path}' not found in repository or insufficient permissions.")
            return
            
        if response.status_code != 200:
            print(f"Error fetching {path}: {response.status_code} - {response.text}")
            return
        
        contents = response.json()
        
        # Handle both single file and directory responses
        if not isinstance(contents, list):
            contents = [contents]
        
        for item in contents:
            item_path = item["path"]
            
            # Calculate relative path if requested
            if use_relative_paths and specific_path:
                # Make sure the path is relative to the specified subdirectory
                if item_path.startswith(specific_path):
                    rel_path = item_path[len(specific_path):].lstrip('/')
                else:
                    rel_path = item_path
            else:
                rel_path = item_path
            
            if item["type"] == "file":
                # Check if file should be included based on patterns
                if not should_include_file(rel_path, item["name"]):
                    print(f"Skipping {rel_path}: Does not match include/exclude patterns")
                    continue
                
                # Check file size if available
                file_size = item.get("size", 0)
                if file_size > max_file_size:
                    skipped_files.append((item_path, file_size))
                    print(f"Skipping {rel_path}: File size ({file_size} bytes) exceeds limit ({max_file_size} bytes)")
                    continue
                
                # For files, get raw content
                if "download_url" in item and item["download_url"]:
                    file_url = item["download_url"]
                    file_response = requests.get(file_url, headers=headers)
                    
                    # Final size check in case content-length header is available but differs from metadata
                    content_length = int(file_response.headers.get('content-length', 0))
                    if content_length > max_file_size:
                        skipped_files.append((item_path, content_length))
                        print(f"Skipping {rel_path}: Content length ({content_length} bytes) exceeds limit ({max_file_size} bytes)")
                        continue
                        
                    if file_response.status_code == 200:
                        files[rel_path] = file_response.text
                        print(f"Downloaded: {rel_path} ({file_size} bytes) ")
                    else:
                        print(f"Failed to download {rel_path}: {file_response.status_code}")
                else:
                    # Alternative method if download_url is not available
                    content_response = requests.get(item["url"], headers=headers)
                    if content_response.status_code == 200:
                        content_data = content_response.json()
                        if content_data.get("encoding") == "base64" and "content" in content_data:
                            # Check size of base64 content before decoding
                            if len(content_data["content"]) * 0.75 > max_file_size:  # Approximate size calculation
                                estimated_size = int(len(content_data["content"]) * 0.75)
                                skipped_files.append((item_path, estimated_size))
                                print(f"Skipping {rel_path}: Encoded content exceeds size limit")
                                continue
                                
                            file_content = base64.b64decode(content_data["content"]).decode('utf-8')
                            files[rel_path] = file_content
                            print(f"Downloaded: {rel_path} ({file_size} bytes)")
                        else:
                            print(f"Unexpected content format for {rel_path}")
                    else:
                        print(f"Failed to get content for {rel_path}: {content_response.status_code}")
            
            elif item["type"] == "dir":
                # Recursively process subdirectories
                fetch_contents(item_path)
    
    # Start crawling from the specified path
    fetch_contents(specific_path)
    
    return {
        "files": files,
        "stats": {
            "downloaded_count": len(files),
            "skipped_count": len(skipped_files),
            "skipped_files": skipped_files,
            "base_path": specific_path if use_relative_paths else None,
            "include_patterns": include_patterns,
            "exclude_patterns": exclude_patterns
        }
    }

# Example usage
if __name__ == "__main__":
    # Get token from environment variable (more secure than hardcoding)
    github_token = os.environ.get("GITHUB_TOKEN")
    
    repo_url = "https://github.com/pydantic/pydantic/tree/6c38dc93f40a47f4d1350adca9ec0d72502e223f/pydantic"
    
    # Example: Get Python and Markdown files, but exclude test files
    result = crawl_github_files(
        repo_url, 
        token=github_token,
        max_file_size=1 * 1024 * 1024,  # 1 MB in bytes
        use_relative_paths=True,  # Enable relative paths
        include_patterns={"*.py", "*.md"},  # Include Python and Markdown files
    )
    
    files = result["files"]
    stats = result["stats"]
    
    print(f"\nDownloaded {stats['downloaded_count']} files.")
    print(f"Skipped {stats['skipped_count']} files due to size limits or patterns.")
    print(f"Base path for relative paths: {stats['base_path']}")
    print(f"Include patterns: {stats['include_patterns']}")
    print(f"Exclude patterns: {stats['exclude_patterns']}")
    
    # Display all file paths in the dictionary
    print("\nFiles in dictionary:")
    for file_path in sorted(files.keys()):
        print(f"  {file_path}")
    
    # Example: accessing content of a specific file
    if files:
        sample_file = next(iter(files))
        print(f"\nSample file: {sample_file}")
        print(f"Content preview: {files[sample_file][:200]}...")