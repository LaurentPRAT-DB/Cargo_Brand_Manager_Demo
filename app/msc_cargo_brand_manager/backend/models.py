from pydantic import BaseModel
from typing import Optional


class KpiItem(BaseModel):
    name: str
    value: float
    target: float
    alert_threshold: float
    status: str  # "green", "amber", "red"
    unit: str  # "%", "x", "#", "score"
    region_detail: Optional[str] = None


class KpiSummaryOut(BaseModel):
    kpis: list[KpiItem]
    period: str


class GenieAskRequest(BaseModel):
    question: str


class GenieFollowupRequest(BaseModel):
    conversation_id: str
    question: str


class GenieResponse(BaseModel):
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    status: str = "UNKNOWN"
    sql: Optional[str] = None
    description: Optional[str] = None
    columns: Optional[list[str]] = None
    data: Optional[list[list]] = None
    row_count: int = 0
    text_response: Optional[str] = None
    error: Optional[str] = None


class EmailDraftRequest(BaseModel):
    recipient: str
    subject: str
    context: str
    tone: str = "professional"


class EmailDraftResponse(BaseModel):
    draft: str
    subject: str


class CampaignOut(BaseModel):
    campaign_id: str
    campaign_name: str
    campaign_type: str
    product_focus: str
    target_segment: str
    budget_usd: float
    start_date: str
    end_date: str
    channel_ids: str


class CampaignRecommendRequest(BaseModel):
    budget_usd: float
    target_segment: str
    product_focus: str
    duration_months: int = 3


class ChannelAllocation(BaseModel):
    channel_name: str
    allocation_pct: float
    budget_usd: float
    expected_roi: float
    rationale: str


class CampaignRecommendResponse(BaseModel):
    allocations: list[ChannelAllocation]
    total_expected_roi: float
    summary: str
