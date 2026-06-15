import asyncio
import hmac
import hashlib
import json
import httpx
from app.core.config import get_settings

async def main():
    settings = get_settings()
    installation_id = 128311577
    repo_full_name = "aarush23g/AI-Code-Review-Assistant-Github"
    pr_number = 14
    
    payload = {
        "action": "opened",
        "pull_request": {
            "number": pr_number,
            "title": f"Test PR: Add vulnerable code",
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
    
    secret = settings.github_webhook_secret
    signature = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()
    signature_header = f"sha256={signature}"

    webhook_url = "http://127.0.0.1:8000/webhooks/github"
    print(f"Sending POST to {webhook_url} for PR #{pr_number}...")
    
    async with httpx.AsyncClient() as client:
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

if __name__ == "__main__":
    asyncio.run(main())
