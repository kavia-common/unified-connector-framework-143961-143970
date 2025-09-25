"""
Webhook stubs for Confluence connector.

Confluence webhooks can be configured for content events. Provide scaffold for registration payload.
"""

from typing import Dict, Any


# PUBLIC_INTERFACE
def build_webhook_registration(callback_url: str, events: list[str]) -> Dict[str, Any]:
    """Return a registration payload for Confluence webhook settings (scaffold)."""
    return {
        "name": "Unified Connector Webhook",
        "url": callback_url,
        "events": events or ["page_created", "page_updated", "comment_created"],
        "excludeBody": False,
    }
