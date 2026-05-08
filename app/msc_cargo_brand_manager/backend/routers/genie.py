import time
import asyncio
import httpx
from fastapi import APIRouter, HTTPException, Request
from databricks.sdk.core import Config
from ..config import settings
from ..models import GenieAskRequest, GenieFollowupRequest, GenieResponse

router = APIRouter(prefix="/api/genie", tags=["genie"])

POLL_INTERVAL = 1.5
MAX_POLL_TIME = 120


def _get_genie_auth() -> tuple[str, dict]:
    """Get host and headers for Genie API using app-level credentials."""
    cfg = Config()
    host = settings.DATABRICKS_HOST or cfg.host
    if host and not host.startswith("http"):
        host = f"https://{host}"
    headers = cfg.authenticate()
    return host, headers


async def _genie_api(method: str, path: str, host: str, headers: dict, json_body: dict | None = None) -> dict:
    url = f"{host}/api/2.0/genie/spaces/{settings.GENIE_SPACE_ID}{path}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        if method == "GET":
            resp = await client.get(url, headers=headers)
        else:
            resp = await client.post(url, headers=headers, json=json_body or {})
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text[:500])
    return resp.json()


async def _poll_message(host: str, headers: dict, conv_id: str, msg_id: str) -> GenieResponse:
    start = time.monotonic()
    while time.monotonic() - start < MAX_POLL_TIME:
        msg = await _genie_api("GET", f"/conversations/{conv_id}/messages/{msg_id}", host, headers)
        status = msg.get("status", "")
        if status not in ("EXECUTING_QUERY", "FETCHING_METADATA", "ASKING_AI", ""):
            result = GenieResponse(
                conversation_id=msg.get("conversation_id") or conv_id,
                message_id=msg.get("id"),
                status=status,
                text_response=msg.get("content"),
            )
            for att in msg.get("attachments", []):
                query = att.get("query")
                if query:
                    result.sql = query.get("query") or query.get("sql")
                    result.description = query.get("description")
                if att.get("text") and not result.text_response:
                    result.text_response = att["text"]
                if status == "COMPLETED" and query and att.get("id"):
                    try:
                        qr = await _genie_api(
                            "GET",
                            f"/conversations/{conv_id}/messages/{msg_id}/query-result/{att['id']}",
                            host, headers,
                        )
                        stmt = qr.get("statement_response", {})
                        cols = [c.get("name", "") for c in stmt.get("manifest", {}).get("schema", {}).get("columns", [])]
                        data = stmt.get("result", {}).get("data_array", [])
                        result.columns = cols
                        result.data = data
                        result.row_count = len(data)
                    except Exception:
                        pass
            return result
        await asyncio.sleep(POLL_INTERVAL)
    return GenieResponse(status="TIMEOUT", error="Genie response timed out")


@router.post("/ask", response_model=GenieResponse, operation_id="askGenie")
async def ask_genie(body: GenieAskRequest, request: Request):
    host, headers = _get_genie_auth()
    resp = await _genie_api("POST", "/start-conversation", host, headers, {"content": body.question})
    conv_id = resp.get("conversation_id")
    msg_id = resp.get("message_id")
    if not conv_id or not msg_id:
        return GenieResponse(status="FAILED", error="Missing IDs in Genie response")
    return await _poll_message(host, headers, conv_id, msg_id)


@router.post("/followup", response_model=GenieResponse, operation_id="followupGenie")
async def followup_genie(body: GenieFollowupRequest, request: Request):
    host, headers = _get_genie_auth()
    resp = await _genie_api(
        "POST", f"/conversations/{body.conversation_id}/messages",
        host, headers, {"content": body.question},
    )
    msg_id = resp.get("message_id") or resp.get("id")
    if not msg_id:
        return GenieResponse(conversation_id=body.conversation_id, status="FAILED", error="Missing message_id")
    return await _poll_message(host, headers, body.conversation_id, msg_id)
