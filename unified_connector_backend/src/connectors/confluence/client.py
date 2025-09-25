"""
Confluence API client with OAuth2 or API key auth, retries, and pagination.

Supports:
- list_spaces (containers)
- list_pages (items)
- list_comments (comments on a page)
- create_page (basic create)

Auth handling mirrors Jira client.
"""

from __future__ import annotations

import asyncio
import base64
import time
from typing import Any, Dict, Optional

import httpx

from src.core.logging_config import get_logger

_logger = get_logger(__name__)


class ConfluenceAuth:
    def __init__(
        self,
        base_url: str,
        method: str,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        api_email: Optional[str] = None,
        api_token: Optional[str] = None,
        token_endpoint: Optional[str] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.method = method
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_email = api_email
        self.api_token = api_token
        self.token_endpoint = token_endpoint or "https://auth.atlassian.com/oauth/token"
        self._exp: Optional[float] = None

    def set_token(self, token: str, expires_in: Optional[int] = None) -> None:
        self.access_token = token
        if expires_in:
            self._exp = time.time() + max(0, expires_in - 30)

    def auth_headers(self) -> Dict[str, str]:
        if self.method == "api_key":
            if not (self.api_email and self.api_token):
                raise ValueError("Missing Confluence API key credentials (email/api_token)")
            basic = base64.b64encode(f"{self.api_email}:{self.api_token}".encode("utf-8")).decode("utf-8")
            return {"Authorization": f"Basic {basic}"}
        if not self.access_token:
            raise ValueError("Missing Confluence access_token for OAuth2 method")
        return {"Authorization": f"Bearer {self.access_token}"}

    async def refresh_if_needed(self, client: httpx.AsyncClient) -> None:
        if self.method != "oauth2":
            return
        if self.access_token and self._exp and time.time() < self._exp:
            return
        if not self.refresh_token:
            return
        _logger.info("Refreshing Confluence OAuth2 token")
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id or "",
            "client_secret": self.client_secret or "",
            "refresh_token": self.refresh_token,
        }
        resp = await client.post(self.token_endpoint, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        resp.raise_for_status()
        payload = resp.json()
        self.set_token(payload.get("access_token"), payload.get("expires_in"))


class ConfluenceClient:
    def __init__(self, auth: ConfluenceAuth, timeout: float = 30.0, max_retries: int = 4, backoff_factor: float = 0.5) -> None:
        self.auth = auth
        self._client = httpx.AsyncClient(timeout=timeout)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    async def close(self) -> None:
        await self._client.aclose()

    def _sleep_delay(self, attempt: int) -> float:
        import random

        return self.backoff_factor * (2 ** (attempt - 1)) + random.random() * 0.25

    async def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None) -> httpx.Response:
        url = f"{self.auth.base_url}{path}"
        attempt = 0
        while True:
            attempt += 1
            await self.auth.refresh_if_needed(self._client)
            headers = {"Accept": "application/json"}
            headers.update(self.auth.auth_headers())
            try:
                resp = await self._client.request(method, url, params=params, json=json, headers=headers)
            except httpx.TimeoutException as e:
                if attempt > self.max_retries:
                    raise e
                await asyncio.sleep(self._sleep_delay(attempt))
                continue

            if resp.status_code in (429, 500, 502, 503, 504):
                if attempt > self.max_retries:
                    resp.raise_for_status()
                retry_after = float(resp.headers.get("Retry-After", "0") or 0.0)
                await asyncio.sleep(max(retry_after, self._sleep_delay(attempt)))
                continue

            return resp

    # Endpoints

    async def list_spaces(self, limit: int = 50, cursor: Optional[str] = None) -> Dict[str, Any]:
        # GET /wiki/api/v2/spaces
        params: Dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        resp = await self._request("GET", "/wiki/api/v2/spaces", params=params)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("results", [])
        next_cursor = None
        if "_links" in data and "next" in data["_links"]:
            # Some deployments return absolute next; we just pass cursor if provided in 'next'
            next_cursor = data["_links"]["next"]
        return {"items": items, "next": next_cursor}

    async def list_pages(self, space_key: Optional[str] = None, limit: int = 50, cursor: Optional[str] = None) -> Dict[str, Any]:
        # GET /wiki/api/v2/pages?spaceId or spaceKey via search
        params: Dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        path = "/wiki/api/v2/pages"
        if space_key:
            # Confluence v2 supports filtering via spaceKey in search endpoint; keep simple using pages with spaceKey query.
            params["spaceKey"] = space_key
        resp = await self._request("GET", path, params=params)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("results", [])
        next_cursor = None
        if "_links" in data and "next" in data["_links"]:
            next_cursor = data["_links"]["next"]
        return {"items": items, "next": next_cursor}

    async def list_comments(self, page_id: str, limit: int = 50, cursor: Optional[str] = None) -> Dict[str, Any]:
        # GET /wiki/api/v2/pages/{id}/comments
        params: Dict[str, Any] = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        resp = await self._request("GET", f"/wiki/api/v2/pages/{page_id}/comments", params=params)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("results", [])
        next_cursor = None
        if "_links" in data and "next" in data["_links"]:
            next_cursor = data["_links"]["next"]
        return {"items": items, "next": next_cursor}

    async def create_page(self, space_key: str, title: str, body: str) -> Dict[str, Any]:
        # POST /wiki/api/v2/pages
        payload = {"spaceKey": space_key, "title": title, "body": {"representation": "storage", "value": body}}
        resp = await self._request("POST", "/wiki/api/v2/pages", json=payload)
        resp.raise_for_status()
        return resp.json()
