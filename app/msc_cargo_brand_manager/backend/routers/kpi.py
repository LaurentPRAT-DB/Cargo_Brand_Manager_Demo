import httpx
from fastapi import APIRouter, Request, HTTPException
from ..config import settings
from ..core import get_databricks_auth
from ..models import KpiItem, KpiSummaryOut

router = APIRouter(prefix="/api/kpi", tags=["kpi"])

KPI_QUERIES = {
    "Unaided Brand Awareness": {
        "sql": """
            SELECT AVG(unaided_awareness_pct) as value
            FROM {catalog}.{schema}.fact_brand_awareness ba
            JOIN {catalog}.{schema}.dim_date d ON ba.date_id = d.date_id
            WHERE d.is_current_period = true
        """,
        "target": 65.0,
        "alert": 50.0,
        "unit": "%",
    },
    "NPS": {
        "sql": """
            SELECT AVG(nps_score) as value
            FROM {catalog}.{schema}.fact_nps n
            JOIN {catalog}.{schema}.dim_date d ON n.date_id = d.date_id
            WHERE d.is_current_period = true
        """,
        "target": 35.0,
        "alert": 25.0,
        "unit": "score",
    },
    "Web Enquiry Conversion": {
        "sql": """
            SELECT AVG(enquiry_conversion_pct) as value
            FROM {catalog}.{schema}.fact_web_performance w
            JOIN {catalog}.{schema}.dim_date d ON w.date_id = d.date_id
            WHERE d.is_current_period = true
        """,
        "target": 2.5,
        "alert": 1.8,
        "unit": "%",
    },
    "Campaign ROI": {
        "sql": """
            SELECT AVG(roi_x) as value
            FROM {catalog}.{schema}.fact_campaign_performance
        """,
        "target": 3.5,
        "alert": 2.5,
        "unit": "x",
    },
    "MQLs per Month": {
        "sql": """
            SELECT AVG(mqls) as value
            FROM {catalog}.{schema}.fact_campaign_performance cp
            JOIN {catalog}.{schema}.dim_date d ON cp.date_id = d.date_id
            WHERE d.is_current_period = true
        """,
        "target": 650.0,
        "alert": 500.0,
        "unit": "#",
    },
    "Share of Voice": {
        "sql": """
            SELECT AVG(share_of_voice_pct) as value
            FROM {catalog}.{schema}.fact_share_of_voice sov
            JOIN {catalog}.{schema}.dim_date d ON sov.date_id = d.date_id
            WHERE d.is_current_period = true AND sov.competitor_name = 'MSC Cargo'
        """,
        "target": 27.0,
        "alert": 20.0,
        "unit": "%",
    },
    "Brand Compliance": {
        "sql": """
            SELECT AVG(overall_score_pct) as value
            FROM {catalog}.{schema}.fact_brand_compliance bc
            JOIN {catalog}.{schema}.dim_date d ON bc.date_id = d.date_id
            WHERE d.is_current_period = true
        """,
        "target": 90.0,
        "alert": 80.0,
        "unit": "%",
    },
    "Email Open Rate": {
        "sql": """
            SELECT AVG(open_rate_pct) as value
            FROM {catalog}.{schema}.fact_email_performance
        """,
        "target": 26.0,
        "alert": 20.0,
        "unit": "%",
    },
    "LinkedIn Engagement": {
        "sql": """
            SELECT AVG(engagement_rate_pct) as value
            FROM {catalog}.{schema}.fact_social_performance sp
            JOIN {catalog}.{schema}.dim_channel ch ON sp.channel_id = ch.channel_id
            WHERE ch.channel_name = 'LinkedIn'
        """,
        "target": 2.5,
        "alert": 1.8,
        "unit": "%",
    },
}


def _get_status(value: float, target: float, alert: float) -> str:
    if value >= target:
        return "green"
    elif value >= alert:
        return "amber"
    return "red"


async def _execute_sql(host: str, token: str, sql: str) -> float:
    url = f"{host}/api/2.0/sql/statements"
    payload = {
        "warehouse_id": settings.WAREHOUSE_ID,
        "statement": sql,
        "wait_timeout": "30s",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers={"Authorization": f"Bearer {token}"}, json=payload)
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text[:300])
    result = resp.json()
    data = result.get("result", {}).get("data_array", [])
    if data and data[0]:
        return float(data[0][0]) if data[0][0] is not None else 0.0
    return 0.0


@router.get("/summary", response_model=KpiSummaryOut, operation_id="getKpiSummary")
async def get_kpi_summary(request: Request):
    host, token = get_databricks_auth(request)
    kpis: list[KpiItem] = []

    for name, config in KPI_QUERIES.items():
        sql = config["sql"].format(catalog=settings.CATALOG, schema=settings.SCHEMA)
        try:
            value = await _execute_sql(host, token, sql)
        except Exception:
            value = 0.0

        kpis.append(KpiItem(
            name=name,
            value=round(value, 1),
            target=config["target"],
            alert_threshold=config["alert"],
            status=_get_status(value, config["target"], config["alert"]),
            unit=config["unit"],
        ))

    return KpiSummaryOut(kpis=kpis, period="Nov 2024 – Apr 2025")
