import os
from fastapi import Request
from databricks.sdk import WorkspaceClient


def get_databricks_auth(request: Request) -> tuple[str, str]:
    """Extract Databricks host and auth token (OBO or SDK fallback)."""
    host = os.getenv("DATABRICKS_HOST", "")
    if host and not host.startswith("http"):
        host = f"https://{host}"

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer "):]
        if token:
            return host, token

    from databricks.sdk.core import Config
    cfg = Config()
    host = host or cfg.host
    headers = cfg.authenticate()
    auth = headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return host, auth[len("Bearer "):]

    raise Exception("No Databricks authentication available")


def get_workspace_client() -> WorkspaceClient:
    """Get a WorkspaceClient using ambient credentials."""
    return WorkspaceClient()
