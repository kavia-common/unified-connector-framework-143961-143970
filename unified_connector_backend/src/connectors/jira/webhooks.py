"""
Webhook stubs for Jira connector.

Jira can send webhooks on issue created/updated/commented. This module provides placeholders for registration and handling.
"""

from typing import Dict, Any


# PUBLIC_INTERFACE
def build_webhook_registration(callback_url: str, events: list[str]) -> Dict[str, Any]:
    """Return the payload that would be used to register a webhook with Jira (example scaffold)."""
    # Jira webhooks are configured in admin; programmatic registration may require app scopes or Connect app.
    return {
        "name": "Unified Connector Webhook",
        "url": callback_url,
        "events": events or ["jira:issue_created", "jira:issue_updated", "comment_created"],
        "excludeBody": False,
    }
