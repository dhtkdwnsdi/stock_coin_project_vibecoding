import json
from github import Github, GithubException
import streamlit as st

@st.cache_resource
def get_github_repo():
    """Initialize and return the GitHub Repository object."""
    token = st.secrets["GITHUB_TOKEN"]
    repo_name = st.secrets["REPO_NAME"]
    
    if not token or not repo_name:
        raise ValueError("GitHub credentials are missing in secrets.")
        
    g = Github(token)
    return g.get_repo(repo_name)

def load_json(file_path: str, default_data: dict) -> dict:
    """Load a JSON file from the repository, returning default_data if not found."""
    repo = get_github_repo()
    try:
        file_content = repo.get_contents(file_path)
        if getattr(file_content, "encoding", None) == "none" or file_content.size > 1000000:
            import base64
            blob = repo.get_git_blob(file_content.sha)
            if blob.encoding == "base64":
                content = base64.b64decode(blob.content).decode("utf-8")
            else:
                content = blob.content
            return json.loads(content)
        else:
            return json.loads(file_content.decoded_content.decode("utf-8"))
    except GithubException as e:
        if e.status == 404: # Not found, create it with default data
            save_json(file_path, default_data, f"Initialize {file_path}")
            return default_data
        else:
            st.error(f"GitHub API Error: {e}")
            return default_data

def save_json(file_path: str, data: dict, commit_message: str):
    """Save a Python dictionary as a JSON file to the repository."""
    repo = get_github_repo()
    content_str = json.dumps(data, ensure_ascii=False, indent=2)
    try:
        file = repo.get_contents(file_path)
        # Update existing file
        repo.update_file(
            file.path,
            commit_message,
            content_str,
            file.sha
        )
    except GithubException as e:
        if e.status == 404:
            # Create new file
            repo.create_file(
                file_path,
                commit_message,
                content_str
            )
        else:
            raise
