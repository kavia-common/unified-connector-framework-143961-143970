"""
Confluence connector adapter implementing BaseConnector.

Implements containers (spaces), items (pages), comments, and basic create (page).
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, Literal, Optional

from src.connectors.base import BaseConnector
from src.core.logging_config import get_logger

from .client import ConfluenceAuth, ConfluenceClient
from .mapping import map_space_to_container, map_page_to_item, map_comment_to_unified
from .types import (
    ConfluenceConnectorConfig,
    ContainersResult,
    ItemsResult,
    CommentsResult,
    CreatePageRequest,
)

_logger = get_logger(__name__)


class ConfluenceConnector(BaseConnector):
    def __init__(self) -> None:
        super().__init__("confluence", "saas", "Confluence")

    # PUBLIC_INTERFACE
    async def validate(self, config: Dict[str, Any]) -> None:
        ConfluenceConnectorConfig.model_validate(config)

    # PUBLIC_INTERFACE
    async def probe(self, config: Dict[str, Any]) -> Dict[str, Any]:
        cfg = ConfluenceConnectorConfig.model_validate(config)
        return {"instance": cfg.base_url, "scopes": cfg.scopes or [], "auth": cfg.auth_method}

    # PUBLIC_INTERFACE
    async def execute(self, job_type: Literal["import", "sync"], config: Dict[str, Any], params: Dict[str, Any]) -> str:
        await asyncio.sleep(0.01)
        return str(uuid.uuid4())

    def example_fields(self) -> Dict[str, Any]:
        return {
            "base_url": "https://your-domain.atlassian.net",
            "auth_method": "oauth2",
            "scopes": ["read:confluence-space.summary", "read:confluence-content.all", "offline_access"],
        }

    async def _client(self, cfg: ConfluenceConnectorConfig) -> ConfluenceClient:
        auth = ConfluenceAuth(
            base_url=cfg.base_url,
            method=cfg.auth_method,
            access_token=cfg.access_token,
            refresh_token=cfg.refresh_token,
            client_id=cfg.client_id,
            client_secret=cfg.client_secret,
            api_email=cfg.api_email,
            api_token=cfg.api_token,
        )
        return ConfluenceClient(auth)

    # PUBLIC_INTERFACE
    async def containers(self, config: Dict[str, Any], limit: int = 50, cursor: Optional[str] = None) -> ContainersResult:
        cfg = ConfluenceConnectorConfig.model_validate(config)
        client = await self._client(cfg)
        try:
            data = await client.list_spaces(limit=limit, cursor=cursor)
            items = [map_space_to_container(s) for s in data.get("items", [])]
            return ContainersResult(items=items, next=data.get("next"))
        finally:
            await client.close()

    # PUBLIC_INTERFACE
    async def items(self, config: Dict[str, Any], container_id: Optional[str] = None, limit: int = 50, cursor: Optional[str] = None) -> ItemsResult:
        cfg = ConfluenceConnectorConfig.model_validate(config)
        client = await self._client(cfg)
        try:
            data = await client.list_pages(space_key=container_id, limit=limit, cursor=cursor)
            items = [map_page_to_item(p) for p in data.get("items", [])]
            return ItemsResult(items=items, next=data.get("next"))
        finally:
            await client.close()

    # PUBLIC_INTERFACE
    async def comments(self, config: Dict[str, Any], item_id: str, limit: int = 50, cursor: Optional[str] = None) -> CommentsResult:
        cfg = ConfluenceConnectorConfig.model_validate(config)
        client = await self._client(cfg)
        try:
            data = await client.list_comments(item_id, limit=limit, cursor=cursor)
            items = [map_comment_to_unified(c) for c in data.get("items", [])]
            return CommentsResult(items=items, next=data.get("next"))
        finally:
            await client.close()

    # PUBLIC_INTERFACE
    async def create(self, config: Dict[str, Any], body: Dict[str, Any]) -> Dict[str, Any]:
        cfg = ConfluenceConnectorConfig.model_validate(config)
        req = CreatePageRequest.model_validate(body)
        client = await self._client(cfg)
        try:
            created = await client.create_page(req.space_key, req.title, req.body)
            return {"id": created.get("id"), "title": created.get("title"), "spaceId": (created.get("space") or {}).get("id")}
        finally:
            await client.close()
