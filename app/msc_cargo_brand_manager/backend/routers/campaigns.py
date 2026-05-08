import httpx
from fastapi import APIRouter, Request, HTTPException
from ..config import settings
from ..core import get_databricks_auth
from ..models import (
    CampaignOut, CampaignRecommendRequest, CampaignRecommendResponse,
    ChannelAllocation,
)

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.get("", response_model=list[CampaignOut], operation_id="listCampaigns")
async def list_campaigns(request: Request):
    host, token = get_databricks_auth(request)
    sql = f"""
        SELECT campaign_id, campaign_name, campaign_type, product_focus,
               target_segment, budget_usd, start_date, end_date, channel_ids
        FROM {settings.CATALOG}.{settings.SCHEMA}.dim_campaign
        ORDER BY start_date DESC
    """
    url = f"{host}/api/2.0/sql/statements"
    payload = {"warehouse_id": settings.WAREHOUSE_ID, "statement": sql, "wait_timeout": "30s"}
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers={"Authorization": f"Bearer {token}"}, json=payload)
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text[:300])

    result = resp.json()
    rows = result.get("result", {}).get("data_array", [])
    return [
        CampaignOut(
            campaign_id=r[0], campaign_name=r[1], campaign_type=r[2],
            product_focus=r[3], target_segment=r[4], budget_usd=float(r[5]),
            start_date=r[6], end_date=r[7], channel_ids=r[8] or "",
        )
        for r in rows
    ]


@router.post("/recommend", response_model=CampaignRecommendResponse, operation_id="recommendCampaign")
async def recommend_campaign(body: CampaignRecommendRequest, request: Request):
    host, token = get_databricks_auth(request)

    # Fetch historical performance by channel
    perf_sql = f"""
        SELECT ch.channel_name, AVG(cp.roi_x) as avg_roi,
               SUM(cp.mqls) as total_mqls, AVG(cp.ctr_pct) as avg_ctr
        FROM {settings.CATALOG}.{settings.SCHEMA}.fact_campaign_performance cp
        JOIN {settings.CATALOG}.{settings.SCHEMA}.dim_channel ch ON cp.channel_id = ch.channel_id
        GROUP BY ch.channel_name
        ORDER BY avg_roi DESC
    """
    url = f"{host}/api/2.0/sql/statements"
    payload = {"warehouse_id": settings.WAREHOUSE_ID, "statement": perf_sql, "wait_timeout": "30s"}
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers={"Authorization": f"Bearer {token}"}, json=payload)

    perf_data = ""
    if resp.status_code < 400:
        rows = resp.json().get("result", {}).get("data_array", [])
        perf_data = "\n".join([f"- {r[0]}: ROI={r[1]}x, MQLs={r[2]}, CTR={r[3]}%" for r in rows])

    # Call LLM for recommendation
    prompt = f"""Based on historical MSC Cargo campaign performance:
{perf_data}

Recommend a channel budget allocation for a new campaign with:
- Budget: ${body.budget_usd:,.0f}
- Target segment: {body.target_segment}
- Product focus: {body.product_focus}
- Duration: {body.duration_months} months

Return a JSON object with this exact structure:
{{"allocations": [{{"channel_name": "...", "allocation_pct": N, "budget_usd": N, "expected_roi": N, "rationale": "..."}}], "total_expected_roi": N, "summary": "..."}}

Use the historical ROI data to inform expected returns. Allocate across 3-5 channels max."""

    llm_payload = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024,
        "temperature": 0.3,
    }
    llm_url = f"{host}/serving-endpoints/{settings.LLM_ENDPOINT}/invocations"
    async with httpx.AsyncClient(timeout=60.0) as client:
        llm_resp = await client.post(llm_url, headers={"Authorization": f"Bearer {token}"}, json=llm_payload)

    if llm_resp.status_code >= 400:
        raise HTTPException(status_code=llm_resp.status_code, detail=f"LLM error: {llm_resp.text[:300]}")

    import json
    content = llm_resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    # Extract JSON from potential markdown code block
    if "```" in content:
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    try:
        rec = json.loads(content.strip())
    except json.JSONDecodeError:
        return CampaignRecommendResponse(
            allocations=[], total_expected_roi=0,
            summary="Failed to parse recommendation. Please try again.",
        )

    return CampaignRecommendResponse(
        allocations=[ChannelAllocation(**a) for a in rec.get("allocations", [])],
        total_expected_roi=rec.get("total_expected_roi", 0),
        summary=rec.get("summary", ""),
    )
