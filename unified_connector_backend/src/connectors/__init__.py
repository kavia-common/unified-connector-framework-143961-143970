"""
Connectors package initializer ensures example and Atlassian connectors are registered on import.
"""

from .registry import registry as _registry

# Make registration lazy to avoid startup blocking
def register_connectors():
    try:
        # Import connectors only when needed
        from .jira.connector import JiraConnector
        from .confluence.connector import ConfluenceConnector
        from . import examples  # Register example connectors
        
        _registry.register(JiraConnector())
        _registry.register(ConfluenceConnector())
        return True
    except Exception as e:
        print(f"Warning: Failed to register connectors: {e}")
        return False

# Export registry for access
__all__ = ['_registry', 'register_connectors']
