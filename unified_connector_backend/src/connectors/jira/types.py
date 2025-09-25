"""
Pydantic types for Jira connector.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl


class JiraConnectorConfig(BaseModel):
    """Configuration for Jira connector."""
    base_url: HttpUrl = Field(..., description="Base URL for Jira Cloud site, e.g., https://your-domain.atlassian.net")
    auth_method: str = Field(..., description="'oauth2' or 'api_key'")
    # OAuth2
    access_token: Optional[str] = Field(default=None)
    refresh_token: Optional[str] = Field(default=None)
    client_id: Optional[str] = Field(default=None)
    client_secret: Optional[str] = Field(default=None)
    # API key method (Basic auth)
    api_email: Optional[str] = Field(default=None, description="Jira account email for API token")
    api_token: Optional[str] = Field(default=None, description="Jira API token")
    # Optional scopes (for probe/UI)
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


class CreateIssueRequest(BaseModel):
    project_key: str = Field(..., description="Jira project key")
    summary: str = Field(..., description="Issue summary")
    description: Optional[str] = Field(default=None)
    issue_type: str = Field(default="Task")
