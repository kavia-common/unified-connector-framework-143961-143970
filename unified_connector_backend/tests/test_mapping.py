"""
Unit tests for mapping helpers that convert provider-native payloads
to unified container/item/comment shapes.

Covers:
- Jira project/issue/comment mapping (including minimal payloads)
- Confluence space/page/comment mapping (including edge handling)
"""

from src.connectors.jira.mapping import (
    map_project_to_container as jira_project_to_container,
    map_issue_to_item as jira_issue_to_item,
    map_comment_to_unified as jira_comment_to_unified,
)
from src.connectors.confluence.mapping import (
    map_space_to_container as conf_space_to_container,
    map_page_to_item as conf_page_to_item,
    map_comment_to_unified as conf_comment_to_unified,
)


def test_jira_project_to_container_basic():
    payload = {"id": "10001", "key": "PRJ", "name": "My Project", "projectTypeKey": "software", "lead": {"displayName": "Ada"}}
    out = jira_project_to_container(payload)
    assert out["id"] == "PRJ"
    assert out["label"] == "My Project"
    assert out["type"] == "project"
    assert out["meta"]["projectTypeKey"] == "software"
    assert out["meta"]["lead"] == "Ada"


def test_jira_issue_to_item_minimal():
    payload = {
        "id": "I-1",
        "key": "PRJ-1",
        "fields": {
            "summary": "Fix bug",
            "project": {"key": "PRJ"},
            "status": {"name": "To Do"},
            "assignee": None,
            "reporter": {"displayName": "Grace"},
            "created": "2024-01-01T00:00:00.000+0000",
            "updated": "2024-01-02T00:00:00.000+0000",
        },
    }
    out = jira_issue_to_item(payload)
    assert out["id"] == "I-1"
    assert out["name"] == "Fix bug"
    assert out["containerId"] == "PRJ"
    assert out["meta"]["status"] == "To Do"
    assert out["meta"]["reporter"] == "Grace"
    assert out["meta"]["key"] == "PRJ-1"


def test_jira_comment_to_unified_handles_text_field():
    payload = {"id": "c1", "author": {"displayName": "Linus"}, "body": "simple text", "created": "t1", "updated": "t2"}
    out = jira_comment_to_unified(payload)
    assert out["id"] == "c1"
    assert out["author"] == "Linus"
    assert out["text"] == "simple text"
    assert out["created"] == "t1"
    assert out["updated"] == "t2"


def test_confluence_space_to_container():
    space = {"id": "10", "key": "DOC", "name": "Docs", "type": "global", "status": "current"}
    out = conf_space_to_container(space)
    assert out["id"] == "DOC"
    assert out["label"] == "Docs"
    assert out["type"] == "space"
    assert out["meta"]["status"] == "current"


def test_confluence_page_to_item_with_space_key():
    page = {
        "id": "123",
        "title": "Welcome",
        "space": {"key": "DOC"},
        "status": "current",
        "version": {"number": 3},
        "createdAt": "2024-02-01T00:00:00Z",
        "parent": {"id": "1"},
    }
    out = conf_page_to_item(page)
    assert out["id"] == "123"
    assert out["name"] == "Welcome"
    assert out["containerId"] == "DOC"
    assert out["meta"]["version"] == 3
    assert out["meta"]["parentId"] == "1"


def test_confluence_comment_to_unified_storage_body():
    comment = {
        "id": "c2",
        "createdBy": {"displayName": "Alice"},
        "body": {"storage": {"value": "<p>Hello</p>"}},
        "createdAt": "t1",
        "updatedAt": "t2",
    }
    out = conf_comment_to_unified(comment)
    assert out["id"] == "c2"
    assert out["author"] == "Alice"
    assert out["text"] == "<p>Hello</p>"
    assert out["created"] == "t1"
    assert out["updated"] == "t2"
