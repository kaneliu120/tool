"""Client for Kane's self-hosted Mem0 (public MCP + optional local REST)."""

from mem0_client.client import (
    DEFAULT_MCP_URL,
    DEFAULT_USER_ID,
    Mem0Client,
    Mem0Config,
    Mem0Error,
)

__all__ = [
    "DEFAULT_MCP_URL",
    "DEFAULT_USER_ID",
    "Mem0Client",
    "Mem0Config",
    "Mem0Error",
]
