"""
Jira API client with OAuth2/API key auth, automatic token refresh, retries, and pagination.

Implements a minimal subset of Jira Cloud v3 REST API used by the connector adapter:
- list_projects (containers)
- list_issues (items)
- list_comments (comments)
- create_issue (basic create)

Auth:
- API Key (email + api_token) using HTTP Basic to get a bearer via PAT? Jira Cloud supports Basic auth directly for REST:
  We support either:
    a) Basic with email:api_token (preferred for API key method)
    b) OAuth2 with access_token and optional refresh_token via Atlassian OAuth 2.0 (3LO)
- For OAuth2, token refresh is performed using configured token endpoint if refresh_token is provided.

Retries:
- Exponential backoff for transient errors (HTTP 429, 5xx)
- Jittered backoff

Pagination:
- Jira uses startAt/maxResults with isLast/total; we wrap into a generator-style page iterator.

Note: This client is a production-grade example scaffold. It does not call live endpoints during CI.
"""

from __future__ import annotations

import asyncio
import base64
import time
from typing import Any, Dict, Generator, List, Optional, Tuple

import httpx

from src.core.logging_config import get_logger

_logger = get_logger(__name__)


class JiraAuth:
    """Holds Jira auth context and provides headers for requests."""

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
        self.method = method  # "oauth2" | "api_key"
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_email = api_email
        self.api_token = api_token
        self.token_endpoint = token_endpoint or "https://auth.atlassian.com/oauth/token"
        self._access_token_exp: Optional[float] = None  # epoch seconds

    def set_token(self, token: str, expires_in: Optional[int] = None) -> None:
        self.access_token = token
        if expires_in:
            self._access_token_exp = time.time() + max(0, expires_in - 30)  # refresh 30s early

    def auth_headers(self) -> Dict[str, str]:
        if self.method == "api_key":
            if not (self.api_email and self.api_token):
                raise ValueError("Missing Jira API key credentials (email/api_token)")
            # Jira Cloud supports basic auth header for API tokens.
            basic = base64.b64encode(f"{self.api_email}:{self.api_token}".encode("utf-8")).decode("utf-8")
            return {"Authorization": f"Basic {basic}"}
        # oauth2
        if not self.access_token:
            raise ValueError("Missing Jira access_token for OAuth2 method")
        return {"Authorization": f"Bearer {self.access_token}"}

    async def refresh_if_needed(self, client: httpx.AsyncClient) -> None:
        """Refresh access token if expired or not present (OAuth2 only)."""
        if self.method != "oauth2":
            return
        if self.access_token and self._access_token_exp and time.time() < self._access_token_exp:
            return
        if not self.refresh_token:
            # No refresh token available
            return
        _logger.info("Refreshing Jira OAuth2 token")
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id or "",
            "client_secret": self.client_secret or "",
            "refresh_token": self.refresh_token,
        }
        resp = await client.post(self.token_endpoint, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        if resp.status_code >= 400:
            _logger.error("Jira token refresh failed: %s %s", resp.status_code, resp.text)
            resp.raise_for_status()
        payload = resp.json()
        self.set_token(payload.get("access_token"), payload.get("expires_in"))


class JiraClient:
    """Jira API client with retry and pagination helpers."""

    def __init__(
        self,
        auth: JiraAuth,
        timeout: float = 30.0,
        max_retries: int = 4,
        backoff_factor: float = 0.5,
    ) -> None:
        self.auth = auth
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self._client = httpx.AsyncClient(timeout=self.timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(
        self, method: str, path: str, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
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
                    _logger.error("Jira request failed after retries: %s %s", resp.status_code, resp.text)
                    resp.raise_for_status()
                retry_after = float(resp.headers.get("Retry-After", "0") or 0.0)
                await asyncio.sleep(max(retry_after, self._sleep_delay(attempt)))
                continue

            if resp.status_code >= 400:
                # Log and raise for caller to normalize
                _logger.warning("Jira error: %s %s -> %s", method, path, resp.text)
            return resp

    def _sleep_delay(self, attempt: int) -> float:
        # exponential backoff with jitter
        import random

        base = self.backoff_factor * (2 ** (attempt - 1))
        return base + random.random() * 0.25

    # Pagination helpers

    async def paged_get(
        self, path: str, query: Optional[Dict[str, Any]] = None, page_size: int = 50, start_at: int = 0, items_key: str = "values"
    ) -> Generator[Tuple[List[Dict[str, Any]], Optional[int]], None, None]:
        """
        Generator that yields (items, next_start_at) until no more items.

        Jira responses often include:
        - startAt, maxResults, isLast, total, and items under a key (e.g., "values" for projects, "issues" for JQL)
        """
        params = dict(query or {})
        params["startAt"] = start_at
        params["maxResults"] = page_size
        while True:
            resp = await self._request("GET", path, params=params)
            resp.raise_for_status()
            data = resp.json()
            # Determine items list
            if "issues" in data:
                items = data.get("issues", [])
                start = data.get("startAt", params["startAt"])
                is_last = (start + len(items)) >= data.get("total", start + len(items))
                next_start = None if is_last else start + len(items)
            else:
                items = data.get(items_key, [])
                start = data.get("startAt", params["startAt"])
                is_last = data.get("isLast", False) or (len(items) < params["maxResults"])
                next_start = None if is_last else start + len(items)
            yield items, next_start
            if next_start is None:
                break
            params["startAt"] = next_start

    # High-level endpoints used by adapter

    async def list_projects(self, page_size: int = 50, start_at: int = 0) -> Dict[str, Any]:
        # GET /rest/api/3/project/search
        items: List[Dict[str, Any]] = []
        next_cursor: Optional[int] = start_at
        async for page_items, next_start in self.paged_get("/rest/api/3/project/search", {}, page_size, start_at, items_key="values"):
            items.extend(page_items)
            next_cursor = next_start
            break  # return single page for route call; adapter can request next via cursor
        return {"items": items, "next": str(next_cursor) if next_cursor is not None else None}

    async def list_issues(
        self, jql: Optional[str] = None, project_key: Optional[str] = None, page_size: int = 50, start_at: int = 0
    ) -> Dict[str, Any]:
        # GET /rest/api/3/search with JQL
        q: Dict[str, Any] = {"startAt": start_at, "maxResults": page_size}
        if jql:
            q["jql"] = jql
        elif project_key:
            q["jql"] = f'project="{project_key}" ORDER BY created DESC'
        resp = await self._request("GET", "/rest/api/3/search", params=q)
        resp.raise_for_status()
        data = resp.json()
        issues = data.get("issues", [])
        start = data.get("startAt", start_at)
        total = data.get("total", start + len(issues))
        next_cursor = None if (start + len(issues)) >= total else (start + len(issues))
        return {"items": issues, "next": str(next_cursor) if next_cursor is not None else None}

    async def list_comments(self, issue_id_or_key: str, page_size: int = 50, start_at: int = 0) -> Dict[str, Any]:
        # GET /rest/api/3/issue/{idOrKey}/comment
        params = {"startAt": start_at, "maxResults": page_size}
        resp = await self._request("GET", f"/rest/api/3/issue/{issue_id_or_key}/comment", params=params)
        resp.raise_for_status()
        data = resp.json()
        comments = data.get("comments", [])
        start = data.get("startAt", start_at)
        total = data.get("total", start + len(comments))
        next_cursor = None if (start + len(comments)) >= total else (start + len(comments))
        return {"items": comments, "next": str(next_cursor) if next_cursor is not None else None}

    async def create_issue(self, project_key: str, summary: str, description: Optional[str] = None, issue_type: str = "Task") -> Dict[str, Any]:
        # POST /rest/api/3/issue
        body = {
            "fields": {
                "summary": summary,
                "issuetype": {"name": issue_type},
                "project": {"key": project_key},
            }
        }
        if description:
            body["fields"]["description"] = description
        resp = await self._request("POST", "/rest/api/3/issue", json=body)
        resp.raise_for_status()
        return resp.json()
