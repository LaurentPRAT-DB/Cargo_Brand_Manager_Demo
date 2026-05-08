import httpx
from fastapi import APIRouter, Request, HTTPException
from ..config import settings
from ..core import get_databricks_auth
from ..models import EmailDraftRequest, EmailDraftResponse

router = APIRouter(prefix="/api/email", tags=["email"])

SYSTEM_PROMPT = """You are a professional email writer for MSC Cargo's brand management team.
Write clear, concise, and actionable emails using shipping/logistics industry terminology.
Format the email body in markdown. Include a greeting and sign-off.
Do not include the subject line in the body — it is provided separately."""


@router.post("/draft", response_model=EmailDraftResponse, operation_id="draftEmail")
async def draft_email(body: EmailDraftRequest, request: Request):
    host, token = get_databricks_auth(request)

    user_prompt = f"""Write a {body.tone} email to {body.recipient} with subject: "{body.subject}"

Context/data to include:
{body.context}

Keep it concise (3-5 paragraphs max). Include specific numbers and data points from the context."""

    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 1024,
        "temperature": 0.7,
    }

    url = f"{host}/serving-endpoints/{settings.LLM_ENDPOINT}/invocations"
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers={"Authorization": f"Bearer {token}"}, json=payload)

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=f"LLM error: {resp.text[:300]}")

    result = resp.json()
    draft = result.get("choices", [{}])[0].get("message", {}).get("content", "")

    return EmailDraftResponse(draft=draft, subject=body.subject)
