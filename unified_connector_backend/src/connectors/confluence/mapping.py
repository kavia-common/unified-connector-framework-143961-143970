"""
Mapping helpers for Confluence to unified models.
"""

from typing import Any, Dict


def map_space_to_container(space: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": space.get("key") or space.get("id"),
        "label": space.get("name"),
        "type": "space",
        "meta": {"type": space.get("type"), "status": space.get("status")},
    }


def map_page_to_item(page: Dict[str, Any]) -> Dict[str, Any]:
    space = page.get("space") or {}
    return {
        "id": page.get("id"),
        "name": page.get("title"),
        "containerId": space.get("key") or space.get("id"),
        "meta": {
            "status": page.get("status"),
            "parentId": (page.get("parent") or {}).get("id"),
            "createdAt": page.get("createdAt"),
            "version": (page.get("version") or {}).get("number"),
        },
    }


def map_comment_to_unified(comment: Dict[str, Any]) -> Dict[str, Any]:
    author = comment.get("createdBy") or {}
    return {
        "id": comment.get("id"),
        "author": author.get("displayName") or author.get("name"),
        "text": (comment.get("body") or {}).get("storage", {}).get("value") if isinstance(comment.get("body"), dict) else comment.get("body"),
        "created": comment.get("createdAt"),
        "updated": comment.get("updatedAt"),
    }
