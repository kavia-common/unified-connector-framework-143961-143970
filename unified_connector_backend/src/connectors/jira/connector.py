"""
Jira connector adapter implementing BaseConnector for Unified Connector Framework.

Exposes:
- validate: checks minimal configuration
- probe: returns scopes/capabilities and instance info
- execute: starts a stub job and returns job id (UUID) (import/sync)
- containers: list projects
- items: list issues (optionally scoped to project)
- comments: list comments for issue
- create: create a basic issue

This file integrates the JiraClient and mapping helpers.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, Literal, Optional

from src.connectors.base import BaseConnector

from src.core.logging_config import get_logger

from .client import JiraAuth, JiraClient
from .mapping import map_project_to_container, map_issue_to_item, map_comment_to_unified
from .types import (
    JiraConnectorConfig,
    ContainersResult,
    ItemsResult,
    CommentsResult,
    CreateIssueRequest,
)

_logger = get_logger(__name__)


class JiraConnector(BaseConnector):
    def __init__(self) -> None:
        super().__init__("jira", "saas", "Jira")

    # PUBLIC_INTERFACE
    async def validate(self, config: Dict[str, Any]) -> None:
        """Validate configuration and raise ValueError on failure."""
        JiraConnectorConfig.model_validate(config)  # raises if invalid

    # PUBLIC_INTERFACE
    async def probe(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Probe provider for capabilities/metadata."""
        cfg = JiraConnectorConfig.model_validate(config)
        # A simple probe returning meta and inferred scopes
        return {
            "scopes": cfg.scopes or [],
            "instance": cfg.base_url,
            "auth": cfg.auth_method,
        }

    # PUBLIC_INTERFACE
    async def execute(self, job_type: Literal["import", "sync"], config: Dict[str, Any], params: Dict[str, Any]) -> str:
        """Start a job and return a job id."""
        # This example does not run background workers; return a stub job id after trivial delay.
        await asyncio.sleep(0.01)
        return str(uuid.uuid4())

    def example_fields(self) -> Dict[str, Any]:
        return {
            "base_url": "https://your-domain.atlassian.net",
            "auth_method": "oauth2",
            "scopes": ["read:jira-work", "write:jira-work", "offline_access"],
        }

    # Additional adapter-style helper methods for routes layer:

    async def _client(self, cfg: JiraConnectorConfig) -> JiraClient:
        auth = JiraAuth(
            base_url=cfg.base_url,
            method=cfg.auth_method,
            access_token=cfg.access_token,
            refresh_token=cfg.refresh_token,
            client_id=cfg.client_id,
            client_secret=cfg.client_secret,
            api_email=cfg.api_email,
            api_token=cfg.api_token,
        )
        return JiraClient(auth)

    # PUBLIC_INTERFACE
    async def containers(self, config: Dict[str, Any], limit: int = 50, cursor: Optional[str] = None) -> ContainersResult:
        """List Jira projects as containers."""
        cfg = JiraConnectorConfig.model_validate(config)
        client = await self._client(cfg)
        try:
            start = int(cursor) if cursor else 0
            data = await client.list_projects(page_size=limit, start_at=start)
            items = [map_project_to_container(p) for p in data.get("items", [])]
            return ContainersResult(items=items, next=data.get("next"))
        finally:
            await client.close()

    # PUBLIC_INTERFACE
    async def items(
        self, config: Dict[str, Any], container_id: Optional[str] = None, limit: int = 50, cursor: Optional[str] = None
    ) -> ItemsResult:
        """List Jira issues (optionally by project key)."""
        cfg = JiraConnectorConfig.model_validate(config)
        client = await self._client(cfg)
        try:
            start = int(cursor) if cursor else 0
            result = await client.list_issues(project_key=container_id, page_size=limit, start_at=start)
            items = [map_issue_to_item(i) for i in result.get("items", [])]
            return ItemsResult(items=items, next=result.get("next"))
        finally:
            await client.close()

    # PUBLIC_INTERFACE
    async def comments(self, config: Dict[str, Any], item_id: str, limit: int = 50, cursor: Optional[str] = None) -> CommentsResult:
        """List comments for a Jira issue."""
        cfg = JiraConnectorConfig.model_validate(config)
        client = await self._client(cfg)
        try:
            start = int(cursor) if cursor else 0
            result = await client.list_comments(item_id, page_size=limit, start_at=start)
            items = [map_comment_to_unified(c) for c in result.get("items", [])]
            return CommentsResult(items=items, next=result.get("next"))
        finally:
            await client.close()

    # PUBLIC_INTERFACE
    async def create(self, config: Dict[str, Any], body: Dict[str, Any]) -> Dict[str, Any]:
        """Create a basic Jira issue."""
        cfg = JiraConnectorConfig.model_validate(config)
        req = CreateIssueRequest.model_validate(body)
        client = await self._client(cfg)
        try:
            created = await client.create_issue(req.project_key, req.summary, req.description, req.issue_type)
            return {"id": created.get("id"), "key": created.get("key"), "self": created.get("self")}
        finally:
            await client.close()
