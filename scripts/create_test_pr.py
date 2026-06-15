import asyncio
import os
import time
import hmac
import hashlib
import json
import httpx
import subprocess
from pathlib import Path
from app.core.config import get_settings
from app.github.client import GitHubAPIClient

async def main():
    settings = get_settings()
    installation_id = 128311577
    repo_full_name = "aarush23g/AI-Code-Review-Assistant-Github"
    
    print("Step 1: Generating installation token...")
    github_client = GitHubAPIClient()
    token = await github_client.get_installation_access_token(installation_id)
    await github_client.close()
    print("Token generated successfully.")

    timestamp = int(time.time())
    branch_name = f"feature/test-bad-code-{timestamp}"

    # Get current branch to return to it later
    print("Getting current branch name...")
    res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True)
    original_branch = res.stdout.strip()
    print(f"Original branch is: {original_branch}")

    try:
        print(f"Step 2: Creating and switching to branch {branch_name}...")
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        
        # Write vulnerable code file in the workspace
        vuln_file = Path("vulnerable_code.py")
        vuln_code = """# Intentionally bad code for AI review testing
password = "admin123"

def execute_query(user_id):
    query = f"SELECT * FROM users WHERE id={user_id}"
    return query
"""
        vuln_file.write_text(vuln_code, encoding="utf-8")

        # Commit and push
        print("Committing changes...")
        subprocess.run(["git", "add", "vulnerable_code.py"], check=True)
        subprocess.run(["git", "commit", "-m", f"Add intentionally bad code for review {timestamp}"], check=True)
        
        print(f"Step 3: Pushing branch {branch_name} to origin...")
        # Push using workspace's authenticated credentials
        subprocess.run(["git", "push", "origin", branch_name], check=True)
        print("Branch pushed successfully.")

        print("Step 4: Creating Pull Request via GitHub API...")
        async with httpx.AsyncClient() as client:
            pr_response = await client.post(
                f"https://api.github.com/repos/{repo_full_name}/pulls",
                headers={
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                json={
                    "title": f"Test PR: Add vulnerable code {timestamp}",
                    "head": branch_name,
                    "base": "master",
                    "body": "This PR contains intentionally bad code (hardcoded password and SQL injection) to test the AI review pipeline.",
                }
            )
            if pr_response.status_code != 201:
                print(f"Failed to create PR: {pr_response.status_code} {pr_response.text}")
                return
            
            pr_data = pr_response.json()
            pr_number = pr_data["number"]
            pr_html_url = pr_data["html_url"]
            print(f"PR created successfully: {pr_html_url} (PR #{pr_number})")

            print("Step 5: Triggering local FastAPI webhook receiver...")
            # Prepare the simulated webhook payload
            payload = {
                "action": "opened",
                "pull_request": {
                    "number": pr_number,
                    "title": f"Test PR: Add vulnerable code {timestamp}",
                    "body": "This PR contains intentionally bad code.",
                    "state": "open",
                },
                "repository": {
                    "full_name": repo_full_name,
                },
                "installation": {
                    "id": installation_id,
                }
            }
            
            payload_bytes = json.dumps(payload).encode("utf-8")
            
            # Calculate HMAC signature
            secret = settings.github_webhook_secret
            signature = hmac.new(
                key=secret.encode("utf-8"),
                msg=payload_bytes,
                digestmod=hashlib.sha256
            ).hexdigest()
            signature_header = f"sha256={signature}"

            # Send POST to local FastAPI server
            webhook_url = "http://127.0.0.1:8000/webhooks/github"
            print(f"Sending POST to {webhook_url}...")
            webhook_response = await client.post(
                webhook_url,
                content=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "pull_request",
                    "X-Hub-Signature-256": signature_header,
                },
                timeout=600.0
            )
            print(f"Webhook status code: {webhook_response.status_code}")
            print("Webhook response content:")
            print(webhook_response.text)

    finally:
        print(f"Cleaning up: Returning to {original_branch} and deleting local test branch...")
        subprocess.run(["git", "checkout", original_branch], check=True)
        # Delete local test branch
        subprocess.run(["git", "branch", "-D", branch_name], check=False)
        # Delete local vulnerable_code.py file if it exists
        if os.path.exists("vulnerable_code.py"):
            os.remove("vulnerable_code.py")
        print("Cleanup completed.")

if __name__ == "__main__":
    asyncio.run(main())
