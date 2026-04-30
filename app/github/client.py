from __future__ import annotations

import base64
from typing import Any

import httpx

from app.github.auth import generate_github_app_jwt


class GitHubAPIClient:
    def __init__(self, base_url: str = "https://api.github.com") -> None:
        self.base_url = base_url

    async def get_installation_access_token(self, installation_id: int) -> str:
        jwt_token = generate_github_app_jwt()

        url = f"{self.base_url}/app/installations/{installation_id}/access_tokens"

        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers)

        response.raise_for_status()
        data = response.json()
        return data["token"]

    async def get_pull_request(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        installation_id: int,
    ) -> dict[str, Any]:
        token = await self.get_installation_access_token(installation_id)

        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}"

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)

        response.raise_for_status()
        return response.json()

    async def get_pull_request_files(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        installation_id: int,
    ) -> list[dict[str, Any]]:
        token = await self.get_installation_access_token(installation_id)

        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}/files"

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        all_files: list[dict[str, Any]] = []
        page = 1

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                response = await client.get(
                    url,
                    headers=headers,
                    params={"per_page": 100, "page": page},
                )
                response.raise_for_status()
                batch = response.json()

                if not batch:
                    break

                all_files.extend(batch)

                if len(batch) < 100:
                    break

                page += 1

        return all_files

    async def get_repository_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str,
        installation_id: int,
    ) -> str | None:
        token = await self.get_installation_access_token(installation_id)

        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                headers=headers,
                params={"ref": ref},
            )

        if response.status_code == 404:
            return None

        response.raise_for_status()
        data = response.json()

        content = data.get("content")
        encoding = data.get("encoding")

        if not content or encoding != "base64":
            return None

        decoded = base64.b64decode(content)
        return decoded.decode("utf-8")

    async def update_issue_comment(
        self,
        owner: str,
        repo: str,
        comment_id: int,
        installation_id: int,
        body: str,
    ) -> dict[str, Any]:
        token = await self.get_installation_access_token(installation_id)

        url = f"{self.base_url}/repos/{owner}/{repo}/issues/comments/{comment_id}"

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.patch(
                url,
                headers=headers,
                json={"body": body},
            )

        response.raise_for_status()
        return response.json()
