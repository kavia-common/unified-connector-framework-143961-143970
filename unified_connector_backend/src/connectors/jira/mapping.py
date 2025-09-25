"""
Mapping helpers: Jira payloads -> Unified connector models for containers/items/comments.
"""

from typing import Any, Dict


def map_project_to_container(project: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map a Jira project to a unified 'container' structure:
    {
      id, label, type
    }
    """
    return {
        "id": project.get("key") or project.get("id"),
        "label": project.get("name"),
        "type": "project",
        "meta": {
            "projectTypeKey": project.get("projectTypeKey"),
            "lead": (project.get("lead") or {}).get("displayName"),
        },
    }


def map_issue_to_item(issue: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map a Jira issue to a unified 'item' structure:
    {
      id, name, containerId, fields...
    }
    """
    fields = issue.get("fields", {})
    proj = fields.get("project") or {}
    return {
        "id": issue.get("id") or issue.get("key"),
        "name": fields.get("summary"),
        "containerId": proj.get("key") or proj.get("id"),
        "meta": {
            "status": (fields.get("status") or {}).get("name"),
            "assignee": (fields.get("assignee") or {}).get("displayName"),
            "reporter": (fields.get("reporter") or {}).get("displayName"),
            "created": fields.get("created"),
            "updated": fields.get("updated"),
            "key": issue.get("key"),
        },
    }


def map_comment_to_unified(comment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map a Jira comment to unified comment:
    {
      id, author, text, created, updated
    }
    """
    author = comment.get("author") or {}
    body = comment.get("body")
    if isinstance(body, dict) and "content" in body:
        # New Atlassian Document Format could be present; fallback to simple text if available
        text = body.get("content") or ""
    else:
        text = body
    return {
        "id": comment.get("id"),
        "author": author.get("displayName"),
        "text": text,
        "created": comment.get("created"),
        "updated": comment.get("updated"),
    }
