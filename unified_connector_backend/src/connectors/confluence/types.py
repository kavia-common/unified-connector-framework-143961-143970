"""
Pydantic types for Confluence connector.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class ConfluenceConnectorConfig(BaseModel):
    base_url: HttpUrl = Field(..., description="Base URL for Confluence Cloud site, e.g., https://your-domain.atlassian.net")
    auth_method: str = Field(..., description="'oauth2' or 'api_key'")
    # OAuth2
    access_token: Optional[str] = Field(default=None)
    refresh_token: Optional[str] = Field(default=None)
    client_id: Optional[str] = Field(default=None)
    client_secret: Optional[str] = Field(default=None)
    # API key
    api_email: Optional[str] = Field(default=None)
    api_token: Optional[str] = Field(default=None)
    scopes: List[str] = Field(default_factory=list)


class ContainersResult(BaseModel):
    items: List[Dict[str, Any]] = Field(default_factory=list)
    next: Optional[str] = Field(default=None)


class ItemsResult(BaseModel):
    items: List[Dict[str, Any]] = Field(default_factory=list)
    next: Optional[str] = Field(default=None)


class CommentsResult(BaseModel):
    items: List[Dict[str, Any]] = Field(default_factory=list)
    next: Optional[str] = Field(default=None)


class CreatePageRequest(BaseModel):
    space_key: str = Field(..., description="Confluence space key")
    title: str = Field(..., description="Page title")
    body: str = Field(..., description="Page body (storage representation)")
