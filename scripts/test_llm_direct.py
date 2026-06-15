import httpx
from app.core.config import get_settings

def main():
    settings = get_settings()
    api_key = settings.openai_api_key
    base_url = settings.openai_base_url or "https://integrate.api.nvidia.com/v1"
    model = settings.openai_model
    
    print(f"URL: {base_url}")
    print(f"API Key: {api_key[:10]}...")
    print(f"Model: {model}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 10
    }
    
    try:
        r = httpx.post(f"{base_url}/chat/completions", headers=headers, json=data, timeout=60.0)
        print(f"Status Code: {r.status_code}")
        print(f"Headers: {dict(r.headers)}")
        print(f"Response: {r.text}")
    except Exception as exc:
        print(f"Exception raised: {type(exc).__name__}: {exc}")

if __name__ == "__main__":
    main()
