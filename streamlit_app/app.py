import os
import time
import json
import requests
import streamlit as st
import pandas as pd
from databricks.sdk.core import Config

st.set_page_config(
    page_title="MSC Cargo Brand Manager",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Configuration ---
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST", "")
GENIE_SPACE_ID = os.getenv("GENIE_SPACE_ID", "")
WAREHOUSE_ID = os.getenv("WAREHOUSE_ID", "")
CATALOG = os.getenv("CATALOG", "serverless_stable_3n0ihb_catalog")
SCHEMA = os.getenv("SCHEMA", "msc_cargo")
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "databricks-claude-sonnet-4")

# --- Custom CSS matching template design ---
st.markdown("""
<style>
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .stSidebar {display: none;}
    .block-container {padding-top: 0 !important; max-width: 1200px;}

    /* Top navigation bar */
    .top-nav {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 999;
        background: #0f172a !important;
        border-bottom: 1px solid #334155;
        padding: 0 2rem;
        height: 90px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .nav-top-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 4px;
    }
    .nav-brand {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .nav-brand-title {
        font-size: 18px;
        font-weight: 700;
        color: #f1f5f9 !important;
        line-height: 1.2;
    }
    .nav-brand-subtitle {
        font-size: 12px;
        color: #94a3b8 !important;
        font-weight: 400;
    }
    .nav-badge {
        background: #fef3cd;
        color: #856404;
        border: 1px solid #f0d68a;
        border-radius: 16px;
        padding: 2px 12px;
        font-size: 11px;
        font-weight: 500;
        margin-left: 12px;
    }
    .nav-right {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .nav-link {
        color: #93c5fd !important;
        font-size: 13px;
        text-decoration: none;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .nav-user {
        background: #1e293b;
        border: 1px solid #475569;
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 12px;
        color: #e2e8f0 !important;
    }
    .nav-tabs {
        display: flex;
        gap: 8px;
        margin-top: 4px;
    }

    /* Main content area - push below fixed nav */
    .main-content {
        margin-top: 100px;
    }

    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #1a2332 0%, #2d3a4a 60%, #3d4f63 100%);
        border-radius: 16px;
        padding: 48px 48px 24px 48px;
        margin-bottom: 32px;
        position: relative;
        overflow: hidden;
        color: white;
    }
    .hero-banner::after {
        content: '';
        position: absolute;
        right: -80px;
        top: -80px;
        width: 400px;
        height: 400px;
        border-radius: 50%;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
    }
    .hero-category {
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 1.5px;
        color: #c5943a;
        text-transform: uppercase;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .hero-category::before {
        content: '';
        display: inline-block;
        width: 32px;
        height: 2px;
        background: #c5943a;
    }
    .hero-title {
        font-size: 32px;
        font-weight: 700;
        color: white;
        margin-bottom: 12px;
        line-height: 1.2;
    }
    .hero-subtitle {
        font-size: 15px;
        color: rgba(255,255,255,0.85) !important;
        margin-bottom: 24px;
        max-width: 600px;
        line-height: 1.5;
    }
    .hero-buttons {
        display: flex;
        gap: 12px;
        margin-bottom: 24px;
    }
    .hero-btn-primary {
        background: #c5943a;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .hero-btn-secondary {
        background: transparent;
        color: white;
        border: 1px solid rgba(255,255,255,0.4);
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .hero-date {
        font-size: 12px;
        color: rgba(255,255,255,0.5);
        padding-top: 16px;
        border-top: 1px solid rgba(255,255,255,0.1);
    }

    /* KPI Section */
    .section-title {
        font-size: 22px;
        font-weight: 700;
        color: #ffffff !important;
        margin-bottom: 4px;
    }
    .section-subtitle {
        font-size: 14px;
        color: #9ca3af !important;
        margin-bottom: 20px;
    }

    /* KPI Cards */
    .kpi-card {
        background: #1e293b !important;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px 24px;
        position: relative;
        overflow: hidden;
        height: 140px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
    }
    .kpi-card.blue::before { background: #2563eb; }
    .kpi-card.gold::before { background: #c5943a; }
    .kpi-card.red::before { background: #dc2626; }
    .kpi-card.green::before { background: #16a34a; }
    .kpi-label {
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.8px;
        color: #94a3b8 !important;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 36px;
        font-weight: 700;
        color: #f1f5f9 !important;
        line-height: 1.1;
        margin-bottom: 8px;
    }
    .kpi-desc {
        font-size: 12px;
        color: #64748b !important;
    }

    /* Activity sections */
    .activity-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }
    .activity-title {
        font-size: 18px;
        font-weight: 700;
        color: #f1f5f9 !important;
    }
    .activity-link {
        color: #2563eb;
        font-size: 13px;
        font-weight: 500;
        text-decoration: none;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .activity-item {
        background: #1e293b !important;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }
    .activity-item-title {
        font-size: 14px;
        font-weight: 600;
        color: #f1f5f9 !important;
        margin-bottom: 4px;
    }
    .activity-item-desc {
        font-size: 12px;
        color: #94a3b8 !important;
    }
    .activity-item-tags {
        display: flex;
        gap: 6px;
        margin-top: 6px;
    }
    .activity-tag {
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 12px;
        font-weight: 500;
    }
    .activity-tag.gold { background: #fef3cd; color: #856404; border: 1px solid #f0d68a; }
    .activity-tag.gray { background: #f3f4f6; color: #374151; border: 1px solid #e5e7eb; }
    .activity-tag.green { background: #d1fae5; color: #065f46; border: 1px solid #a7f3d0; }
    .activity-item-stat {
        text-align: right;
        min-width: 60px;
    }
    .activity-item-stat-value {
        font-size: 16px;
        font-weight: 700;
        color: #f1f5f9 !important;
    }
    .activity-item-stat-label {
        font-size: 11px;
        color: #64748b !important;
    }

    /* Floating Ask Genie button */
    .floating-genie {
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 1000;
        background: #1a2332;
        color: white;
        border-radius: 24px;
        padding: 12px 20px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        display: flex;
        align-items: center;
        gap: 8px;
        border: none;
    }

    /* Navigation button styling */
    div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
        background: transparent !important;
        border: none !important;
        border-bottom: 2px solid transparent !important;
        border-radius: 0 !important;
        color: #e2e8f0 !important;
        font-weight: 500;
    }
    div[data-testid="stHorizontalBlock"] button[kind="primary"] {
        background: transparent !important;
        border: none !important;
        border-bottom: 2px solid #93c5fd !important;
        border-radius: 0 !important;
        color: #ffffff !important;
        font-weight: 600;
    }
    div[data-testid="stHorizontalBlock"] button p {
        color: inherit !important;
    }

    /* Chat styling */
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #64748b !important;
        font-size: 12px;
        padding: 32px 0 16px 0;
        border-top: 1px solid #334155;
        margin-top: 48px;
    }

    /* Override Streamlit defaults */
    .stMetric { display: none; }
    div[data-testid="stVerticalBlock"] > div {gap: 0.5rem;}

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .hero-banner { padding: 32px 24px 16px 24px; }
        .hero-title { font-size: 24px; }
        .kpi-card { height: auto; }
    }
</style>
""", unsafe_allow_html=True)


# --- Backend Functions ---
def get_auth():
    """Get Databricks host and auth headers using app service principal."""
    cfg = Config()
    host = DATABRICKS_HOST or cfg.host
    if host and not host.startswith("http"):
        host = f"https://{host}"
    headers = cfg.authenticate()
    return host, headers


def execute_sql(sql: str) -> list:
    """Execute SQL and return data_array."""
    host, headers = get_auth()
    resp = requests.post(
        f"{host}/api/2.0/sql/statements",
        headers=headers,
        json={"warehouse_id": WAREHOUSE_ID, "statement": sql, "wait_timeout": "30s"},
    )
    if resp.status_code >= 400:
        return []
    result = resp.json()
    state = result.get("status", {}).get("state", "")
    if state == "FAILED":
        return []
    return result.get("result", {}).get("data_array", [])


def execute_sql_with_columns(sql: str) -> tuple[list, list]:
    """Execute SQL and return (columns, data_array)."""
    host, headers = get_auth()
    resp = requests.post(
        f"{host}/api/2.0/sql/statements",
        headers=headers,
        json={"warehouse_id": WAREHOUSE_ID, "statement": sql, "wait_timeout": "30s"},
    )
    if resp.status_code >= 400:
        return [], []
    result = resp.json()
    state = result.get("status", {}).get("state", "")
    if state == "FAILED":
        return [], []
    columns = [c.get("name", "") for c in result.get("manifest", {}).get("schema", {}).get("columns", [])]
    data = result.get("result", {}).get("data_array", [])
    return columns, data


def ask_genie(question: str, conversation_id: str | None = None) -> dict:
    """Ask Genie Space a question."""
    host, headers = get_auth()
    base = f"{host}/api/2.0/genie/spaces/{GENIE_SPACE_ID}"

    if conversation_id:
        resp = requests.post(
            f"{base}/conversations/{conversation_id}/messages",
            headers=headers, json={"content": question},
        )
        if resp.status_code >= 400:
            return {"status": "FAILED", "error": f"API error: {resp.text[:200]}"}
        data = resp.json()
        msg_id = data.get("message_id") or data.get("id")
    else:
        resp = requests.post(
            f"{base}/start-conversation",
            headers=headers, json={"content": question},
        )
        if resp.status_code >= 400:
            return {"status": "FAILED", "error": f"API error: {resp.text[:200]}"}
        data = resp.json()
        conversation_id = data.get("conversation_id")
        msg_id = data.get("message_id")

    if not conversation_id or not msg_id:
        return {"status": "FAILED", "error": f"Missing IDs. Response: {data}"}

    PENDING_STATUSES = {"EXECUTING_QUERY", "FETCHING_METADATA", "ASKING_AI", "SUBMITTED", "FILTERING", "PENDING", ""}
    time.sleep(2)
    for _ in range(80):
        poll_resp = requests.get(
            f"{base}/conversations/{conversation_id}/messages/{msg_id}",
            headers=headers,
        )
        if poll_resp.status_code >= 400:
            time.sleep(2)
            continue
        msg = poll_resp.json()
        status = msg.get("status", "")
        if status not in PENDING_STATUSES:
            result = {
                "conversation_id": conversation_id,
                "status": status,
                "text_response": None,
                "sql": None,
                "columns": None,
                "data": None,
            }
            for att in msg.get("attachments", []):
                query = att.get("query")
                if query:
                    result["sql"] = query.get("query") or query.get("sql")
                    result["text_response"] = query.get("description")
                    att_id = att.get("id")
                    if status == "COMPLETED" and att_id:
                        qr_resp = requests.get(
                            f"{base}/conversations/{conversation_id}/messages/{msg_id}/query-result/{att_id}",
                            headers=headers,
                        )
                        if qr_resp.status_code < 400:
                            qr = qr_resp.json()
                            stmt = qr.get("statement_response", {})
                            cols = [c.get("name", "") for c in stmt.get("manifest", {}).get("schema", {}).get("columns", [])]
                            data_rows = stmt.get("result", {}).get("data_array", [])
                            if cols and data_rows:
                                result["columns"] = cols
                                result["data"] = data_rows
                text_att = att.get("text")
                if text_att:
                    if isinstance(text_att, dict):
                        result["text_response"] = text_att.get("content", "")
                    elif isinstance(text_att, str):
                        result["text_response"] = text_att

            if result["sql"] and not result["data"]:
                cols, rows = execute_sql_with_columns(result["sql"])
                if cols and rows:
                    result["columns"] = cols
                    result["data"] = rows

            if not result["text_response"]:
                content = msg.get("content", "")
                if content and content != question:
                    result["text_response"] = content

            return result
        time.sleep(2)
    return {"status": "TIMEOUT", "error": "Timed out", "conversation_id": conversation_id}


def call_llm(messages: list, max_tokens: int = 1024, temperature: float = 0.7) -> str:
    """Call Foundation Model endpoint."""
    host, headers = get_auth()
    resp = requests.post(
        f"{host}/serving-endpoints/{LLM_ENDPOINT}/invocations",
        headers=headers,
        json={"messages": messages, "max_tokens": max_tokens, "temperature": temperature},
    )
    if resp.status_code >= 400:
        return f"Error: {resp.text[:200]}"
    return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")


# --- KPI Definitions ---
KPI_DEFS = [
    ("Unaided Brand Awareness", f"SELECT AVG(unaided_awareness_pct) FROM {CATALOG}.{SCHEMA}.fact_brand_awareness ba JOIN {CATALOG}.{SCHEMA}.dim_date d ON ba.date_id=d.date_id WHERE d.is_current_period=true", 65.0, 50.0, "%", "blue", "Current period avg"),
    ("NPS Score", f"SELECT AVG(nps_score) FROM {CATALOG}.{SCHEMA}.fact_nps n JOIN {CATALOG}.{SCHEMA}.dim_date d ON n.date_id=d.date_id WHERE d.is_current_period=true", 35.0, 25.0, "", "blue", "Net Promoter Score"),
    ("Web Enquiry Conversion", f"SELECT AVG(enquiry_conversion_pct) FROM {CATALOG}.{SCHEMA}.fact_web_performance w JOIN {CATALOG}.{SCHEMA}.dim_date d ON w.date_id=d.date_id WHERE d.is_current_period=true", 2.5, 1.8, "%", "blue", "Enquiry to quote rate"),
    ("Campaign ROI", f"SELECT AVG(roi_x) FROM {CATALOG}.{SCHEMA}.fact_campaign_performance", 3.5, 2.5, "x", "gold", "Average across campaigns"),
    ("MQLs per Month", f"SELECT AVG(mqls) FROM {CATALOG}.{SCHEMA}.fact_campaign_performance cp JOIN {CATALOG}.{SCHEMA}.dim_date d ON cp.date_id=d.date_id WHERE d.is_current_period=true", 650.0, 500.0, "", "gold", "Marketing qualified leads"),
    ("Share of Voice", f"SELECT AVG(share_of_voice_pct) FROM {CATALOG}.{SCHEMA}.fact_share_of_voice sov JOIN {CATALOG}.{SCHEMA}.dim_date d ON sov.date_id=d.date_id WHERE d.is_current_period=true AND sov.competitor_name='MSC Cargo'", 27.0, 20.0, "%", "gold", "vs competitors in market"),
    ("Brand Compliance", f"SELECT AVG(overall_score_pct) FROM {CATALOG}.{SCHEMA}.fact_brand_compliance bc JOIN {CATALOG}.{SCHEMA}.dim_date d ON bc.date_id=d.date_id WHERE d.is_current_period=true", 90.0, 80.0, "%", "green", "Global brand audit score"),
    ("Email Open Rate", f"SELECT AVG(open_rate_pct) FROM {CATALOG}.{SCHEMA}.fact_email_performance", 26.0, 20.0, "%", "green", "All email campaigns"),
    ("LinkedIn Engagement", f"SELECT AVG(engagement_rate_pct) FROM {CATALOG}.{SCHEMA}.fact_social_performance sp JOIN {CATALOG}.{SCHEMA}.dim_channel ch ON sp.channel_id=ch.channel_id WHERE ch.channel_name='LinkedIn'", 2.5, 1.8, "%", "red", "Engagement rate"),
]


# --- Get user info ---
user_email = ""
try:
    user_email = st.context.headers.get("X-Forwarded-Email", "")
except Exception:
    pass
user_display = user_email or "Brand Manager"

# --- Top Navigation ---
genie_url = f"https://fevm-serverless-stable-3n0ihb.cloud.databricks.com/genie/rooms/{GENIE_SPACE_ID}?o=7474645572615955" if GENIE_SPACE_ID else "#"
st.markdown(f"""
<div class="top-nav">
    <div class="nav-top-row">
        <div class="nav-brand">
            <span style="font-size:24px;">🚢</span>
            <div>
                <div class="nav-brand-title">Brand Manager</div>
                <div class="nav-brand-subtitle">MSC Cargo · Global Logistics</div>
            </div>
            <span class="nav-badge">Synthetic data — demo only</span>
        </div>
        <div class="nav-right">
            <a href="{genie_url}" target="_blank" class="nav-link">Genie space ↗</a>
            <span class="nav-user">{user_display}</span>
        </div>
    </div>
</div>
<div class="main-content"></div>
""", unsafe_allow_html=True)

# Add spacer for fixed nav
st.markdown("<div style='height: 90px'></div>", unsafe_allow_html=True)

# --- Page Navigation (session state based) ---
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"

# Check query params for deep linking
params = st.query_params
if params.get("page"):
    st.session_state.current_page = params["page"]
    st.query_params.clear()

# Navigation tabs as columns of buttons
nav_pages = ["Home", "Ask Genie", "Email Composer", "Campaign Planner"]
nav_icons = ["🏠", "💬", "✉️", "🎯"]
nav_cols = st.columns(len(nav_pages))
for i, (page_name, icon) in enumerate(zip(nav_pages, nav_icons)):
    with nav_cols[i]:
        is_active = st.session_state.current_page == page_name
        if st.button(
            f"{icon} {page_name}",
            key=f"nav_{page_name}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state.current_page = page_name
            st.rerun()

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

current_page = st.session_state.current_page

# === PAGE: HOME ===
if current_page == "Home":
    # Hero Banner
    st.markdown(f"""
    <div class="hero-banner">
        <div class="hero-category">GLOBAL LOGISTICS · BRAND MANAGEMENT</div>
        <div class="hero-title">Welcome back to MSC Cargo Brand Manager.</div>
        <div class="hero-subtitle">
            Monitor brand KPIs across regions, forecast campaign performance, and draft
            on-brand communications with Claude. All numbers live from your Databricks warehouse.
        </div>
        <div class="hero-date">As of 2026-05-08 · Reporting period: Nov 2024 – Apr 2025</div>
    </div>
    """, unsafe_allow_html=True)


    # Performance Section
    st.markdown("""
    <div class="section-title">Performance</div>
    <div class="section-subtitle">Live numbers from the data warehouse</div>
    """, unsafe_allow_html=True)

    # KPI Cards - Row 1 (first 4)
    kpi_cols_1 = st.columns(4)
    for i in range(4):
        with kpi_cols_1[i]:
            name, sql, target, alert, unit, color, desc = KPI_DEFS[i]
            data = execute_sql(sql)
            value = float(data[0][0]) if data and data[0] and data[0][0] else 0.0
            value = round(value, 1)

            # Determine card color based on status
            if value < alert:
                card_color = "red"
            elif value >= target:
                card_color = color
            else:
                card_color = "gold"

            if unit == "%":
                fmt_value = f"{value}%"
            elif unit == "x":
                fmt_value = f"{value}x"
            elif value >= 1000:
                fmt_value = f"{value:,.0f}"
            else:
                fmt_value = f"{value}"

            st.markdown(f"""
            <div class="kpi-card {card_color}">
                <div class="kpi-label">{name}</div>
                <div class="kpi-value">{fmt_value}</div>
                <div class="kpi-desc">{desc} · Target: {target}{unit}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # KPI Cards - Row 2 (next 4-5)
    kpi_cols_2 = st.columns(4)
    for i in range(4, min(8, len(KPI_DEFS))):
        with kpi_cols_2[i - 4]:
            name, sql, target, alert, unit, color, desc = KPI_DEFS[i]
            data = execute_sql(sql)
            value = float(data[0][0]) if data and data[0] and data[0][0] else 0.0
            value = round(value, 1)

            if value < alert:
                card_color = "red"
            elif value >= target:
                card_color = color
            else:
                card_color = "gold"

            if unit == "%":
                fmt_value = f"{value}%"
            elif unit == "x":
                fmt_value = f"{value}x"
            elif value >= 1000:
                fmt_value = f"{value:,.0f}"
            else:
                fmt_value = f"{value}"

            st.markdown(f"""
            <div class="kpi-card {card_color}">
                <div class="kpi-label">{name}</div>
                <div class="kpi-value">{fmt_value}</div>
                <div class="kpi-desc">{desc} · Target: {target}{unit}</div>
            </div>
            """, unsafe_allow_html=True)

    # If there's a 9th KPI, show it
    if len(KPI_DEFS) > 8:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        kpi_cols_3 = st.columns(4)
        with kpi_cols_3[0]:
            name, sql, target, alert, unit, color, desc = KPI_DEFS[8]
            data = execute_sql(sql)
            value = float(data[0][0]) if data and data[0] and data[0][0] else 0.0
            value = round(value, 1)

            if value < alert:
                card_color = "red"
            elif value >= target:
                card_color = color
            else:
                card_color = "gold"

            if unit == "%":
                fmt_value = f"{value}%"
            elif unit == "x":
                fmt_value = f"{value}x"
            elif value >= 1000:
                fmt_value = f"{value:,.0f}"
            else:
                fmt_value = f"{value}"

            st.markdown(f"""
            <div class="kpi-card {card_color}">
                <div class="kpi-label">{name}</div>
                <div class="kpi-value">{fmt_value}</div>
                <div class="kpi-desc">{desc} · Target: {target}{unit}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # Two-column activity section
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("""
        <div class="activity-header">
            <span class="activity-title">Recent campaigns</span>
            <span class="activity-link">View all →</span>
        </div>
        """, unsafe_allow_html=True)

        campaign_sql = f"""
            SELECT campaign_name, campaign_type, target_segment, budget_usd
            FROM {CATALOG}.{SCHEMA}.dim_campaign
            ORDER BY start_date DESC LIMIT 5
        """
        campaigns = execute_sql(campaign_sql)
        for row in campaigns:
            name_val = row[0] if row[0] else "Untitled"
            ctype = row[1] if row[1] else ""
            segment = row[2] if row[2] else ""
            budget_val = float(row[3]) if row[3] else 0
            budget_fmt = f"${budget_val/1000:.0f}K" if budget_val >= 1000 else f"${budget_val:.0f}"

            st.markdown(f"""
            <div class="activity-item">
                <div>
                    <div class="activity-item-title">{name_val}</div>
                    <div class="activity-item-desc">{segment}</div>
                    <div class="activity-item-tags">
                        <span class="activity-tag gold">{ctype}</span>
                    </div>
                </div>
                <div class="activity-item-stat">
                    <div class="activity-item-stat-value">{budget_fmt}</div>
                    <div class="activity-item-stat-label">budget</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        if not campaigns:
            st.info("No campaigns found")

    with col_right:
        st.markdown("""
        <div class="activity-header">
            <span class="activity-title">Top performers by channel</span>
            <span class="activity-link">Full report →</span>
        </div>
        """, unsafe_allow_html=True)

        perf_sql = f"""
            SELECT ch.channel_name, ROUND(AVG(cp.roi_x), 1) as avg_roi, SUM(cp.mqls) as total_mqls
            FROM {CATALOG}.{SCHEMA}.fact_campaign_performance cp
            JOIN {CATALOG}.{SCHEMA}.dim_channel ch ON cp.channel_id=ch.channel_id
            GROUP BY ch.channel_name
            ORDER BY AVG(cp.roi_x) DESC LIMIT 5
        """
        perf_rows = execute_sql(perf_sql)
        for row in perf_rows:
            ch_name = row[0] if row[0] else ""
            roi_val = row[1] if row[1] else "0"
            mqls_val = int(float(row[2])) if row[2] else 0
            mqls_fmt = f"{mqls_val:,}" if mqls_val < 10000 else f"{mqls_val/1000:.0f}K"

            roi_float = float(roi_val)
            tag_color = "green" if roi_float >= 3.5 else "gold" if roi_float >= 2.5 else "gray"

            st.markdown(f"""
            <div class="activity-item">
                <div>
                    <div class="activity-item-title">{ch_name}</div>
                    <div class="activity-item-desc">{mqls_fmt} MQLs generated</div>
                    <div class="activity-item-tags">
                        <span class="activity-tag {tag_color}">{roi_val}x ROI</span>
                    </div>
                </div>
                <div class="activity-item-stat">
                    <div class="activity-item-stat-value">{roi_val}x</div>
                    <div class="activity-item-stat-label">avg ROI</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        if not perf_rows:
            st.info("No performance data available")

    # Footer
    st.markdown("""
    <div class="footer">
        MSC Cargo Brand Manager · Data on Databricks · Internal demo only
    </div>
    """, unsafe_allow_html=True)


# === PAGE: ASK GENIE ===
elif current_page == "Ask Genie":
    st.markdown("""
    <div class="section-title">Ask Genie</div>
    <div class="section-subtitle">Ask natural language questions about MSC Cargo brand performance</div>
    """, unsafe_allow_html=True)

    if "genie_messages" not in st.session_state:
        st.session_state.genie_messages = []
    if "genie_conv_id" not in st.session_state:
        st.session_state.genie_conv_id = None

    def display_genie_result(result: dict):
        """Display Genie response: text, table, and chart."""
        content = result.get("text_response") or result.get("error") or "No response"
        st.markdown(content)

        if result.get("data") and result.get("columns"):
            df = pd.DataFrame(result["data"], columns=result["columns"])
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    pass

            st.dataframe(df, use_container_width=True, hide_index=True)

            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            non_numeric_cols = [c for c in df.columns if c not in numeric_cols]

            if numeric_cols and non_numeric_cols and len(df) > 1:
                label_col = non_numeric_cols[0]
                chart_df = df.set_index(label_col)[numeric_cols]
                if len(df) <= 20:
                    st.bar_chart(chart_df)
                else:
                    st.line_chart(chart_df)

        if result.get("sql"):
            with st.expander("View SQL Query"):
                st.code(result["sql"], language="sql")

    # Display chat history
    for msg in st.session_state.genie_messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                st.write(msg["content"])
            else:
                display_genie_result(msg)

    # Suggestions when empty
    if not st.session_state.genie_messages:
        st.markdown("**Try asking:**")
        suggestions = [
            "What is the average NPS by region?",
            "Which campaign had the worst ROI?",
            "How is our share of voice trending vs Maersk?",
        ]
        suggestion_cols = st.columns(len(suggestions))
        for i, s in enumerate(suggestions):
            if suggestion_cols[i].button(s, key=f"sug_{i}"):
                st.session_state.genie_pending = s
                st.rerun()

    # Handle pending suggestion
    if "genie_pending" in st.session_state:
        prompt = st.session_state.pop("genie_pending")
        st.session_state.genie_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Querying Genie..."):
                result = ask_genie(prompt, st.session_state.genie_conv_id)
                st.session_state.genie_conv_id = result.get("conversation_id")
                display_genie_result(result)
                st.session_state.genie_messages.append({
                    "role": "assistant",
                    "content": result.get("text_response") or result.get("error") or "No response",
                    "text_response": result.get("text_response"),
                    "sql": result.get("sql"),
                    "columns": result.get("columns"),
                    "data": result.get("data"),
                    "error": result.get("error"),
                })

    # Chat input
    if prompt := st.chat_input("Ask about brand performance..."):
        st.session_state.genie_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Querying Genie..."):
                result = ask_genie(prompt, st.session_state.genie_conv_id)
                st.session_state.genie_conv_id = result.get("conversation_id")
                display_genie_result(result)
                st.session_state.genie_messages.append({
                    "role": "assistant",
                    "content": result.get("text_response") or result.get("error") or "No response",
                    "text_response": result.get("text_response"),
                    "sql": result.get("sql"),
                    "columns": result.get("columns"),
                    "data": result.get("data"),
                    "error": result.get("error"),
                })

    # New conversation button
    if st.session_state.genie_conv_id:
        if st.button("🔄 New Conversation"):
            st.session_state.genie_messages = []
            st.session_state.genie_conv_id = None
            st.rerun()


# === PAGE: EMAIL COMPOSER ===
elif current_page == "Email Composer":
    st.markdown("""
    <div class="section-title">Email Composer</div>
    <div class="section-subtitle">Generate professional, data-driven communications with Claude</div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        recipient = st.text_input("Recipient", placeholder="e.g., Regional VP South Asia")
        subject = st.text_input("Subject", placeholder="e.g., NPS Performance Review — Action Required")
        tone = st.selectbox("Tone", ["professional", "urgent", "congratulatory", "executive-summary"])
        context = st.text_area(
            "Context / Data Points",
            height=200,
            placeholder="Paste KPI data or Genie insights here...\ne.g., NPS in South Asia dropped to 18 (target: 35). Top negative driver: documentation complexity.",
        )

        if st.button("Generate Draft", type="primary", disabled=not all([recipient, subject, context])):
            with st.spinner("Generating..."):
                system = """You are a professional email writer for MSC Cargo's brand management team.
Write clear, concise, and actionable emails using shipping/logistics industry terminology.
Format the email body in markdown. Include a greeting and sign-off.
Do not include the subject line in the body."""
                user_prompt = f"""Write a {tone} email to {recipient} with subject: "{subject}"

Context/data to include:
{context}

Keep it concise (3-5 paragraphs max). Include specific numbers and data points from the context."""
                draft = call_llm([
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt},
                ])
                st.session_state.email_draft = draft

    with col2:
        st.markdown("**Email Preview**")
        if "email_draft" in st.session_state and st.session_state.email_draft:
            st.markdown(st.session_state.email_draft)
            st.markdown("---")
            if st.button("📋 Copy to Clipboard"):
                st.code(st.session_state.email_draft)
                st.success("Draft displayed — copy from above")
        else:
            st.markdown("""
            <div style="background:#f9fafb; border:1px solid #e5e7eb; border-radius:12px; padding:48px 24px; text-align:center; color:#9ca3af;">
                <div style="font-size:32px; margin-bottom:12px;">✉️</div>
                <div>Your generated email will appear here</div>
            </div>
            """, unsafe_allow_html=True)


# === PAGE: CAMPAIGN PLANNER ===
elif current_page == "Campaign Planner":
    st.markdown("""
    <div class="section-title">Campaign Planner</div>
    <div class="section-subtitle">Plan new campaigns with AI-powered budget recommendations</div>
    """, unsafe_allow_html=True)

    # Show existing campaigns
    st.markdown("#### Active Campaigns")
    campaign_sql = f"""
        SELECT campaign_name, campaign_type, product_focus, target_segment,
               budget_usd, start_date, end_date
        FROM {CATALOG}.{SCHEMA}.dim_campaign ORDER BY start_date DESC
    """
    rows = execute_sql(campaign_sql)
    if rows:
        df = pd.DataFrame(rows, columns=["Campaign", "Type", "Product", "Segment", "Budget", "Start", "End"])
        df["Budget"] = df["Budget"].astype(float).apply(lambda x: f"${x:,.0f}")
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()

    # New campaign recommendation
    st.markdown("#### Plan New Campaign")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        budget = st.number_input("Budget (USD)", min_value=50000, max_value=1000000, value=200000, step=10000)
    with col2:
        segment = st.selectbox("Target Segment", ["Freight Forwarders", "Food & Pharma Exporters", "New Prospects", "Specialist Forwarders"])
    with col3:
        product = st.selectbox("Product Focus", ["All Products", "Reefer Cargo", "Dry Container", "DG Cargo"])
    with col4:
        duration = st.selectbox("Duration", [1, 2, 3, 6], index=2, format_func=lambda x: f"{x} month{'s' if x>1 else ''}")

    if st.button("Get AI Recommendation", type="primary"):
        with st.spinner("Analyzing historical performance..."):
            perf_sql = f"""
                SELECT ch.channel_name, AVG(cp.roi_x), SUM(cp.mqls), AVG(cp.ctr_pct)
                FROM {CATALOG}.{SCHEMA}.fact_campaign_performance cp
                JOIN {CATALOG}.{SCHEMA}.dim_channel ch ON cp.channel_id=ch.channel_id
                GROUP BY ch.channel_name ORDER BY AVG(cp.roi_x) DESC
            """
            perf_rows = execute_sql(perf_sql)
            perf_data = "\n".join([f"- {r[0]}: ROI={r[1]}x, MQLs={r[2]}, CTR={r[3]}%" for r in perf_rows])

            prompt = f"""Based on historical MSC Cargo campaign performance:
{perf_data}

Recommend a channel budget allocation for a new campaign with:
- Budget: ${budget:,.0f}
- Target segment: {segment}
- Product focus: {product}
- Duration: {duration} months

Return ONLY a JSON object with this structure:
{{"allocations": [{{"channel_name": "...", "allocation_pct": N, "budget_usd": N, "expected_roi": N, "rationale": "..."}}], "total_expected_roi": N, "summary": "..."}}

Use the historical ROI data to inform expected returns. Allocate across 3-5 channels max."""

            response = call_llm([{"role": "user", "content": prompt}], temperature=0.3)

            content = response
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            try:
                rec = json.loads(content.strip())
            except json.JSONDecodeError:
                st.error("Failed to parse recommendation. Raw response:")
                st.code(response)
                rec = None

            if rec and rec.get("allocations"):
                st.success(f"**Expected Total ROI: {rec['total_expected_roi']}x**")
                st.markdown(rec.get("summary", ""))

                alloc_df = pd.DataFrame(rec["allocations"])
                alloc_df["budget_usd"] = alloc_df["budget_usd"].apply(lambda x: f"${x:,.0f}")
                alloc_df["expected_roi"] = alloc_df["expected_roi"].apply(lambda x: f"{x}x")
                alloc_df["allocation_pct"] = alloc_df["allocation_pct"].apply(lambda x: f"{x}%")
                alloc_df.columns = ["Channel", "Allocation", "Budget", "Expected ROI", "Rationale"]
                st.dataframe(alloc_df, use_container_width=True, hide_index=True)

                chart_df = pd.DataFrame(rec["allocations"])[["channel_name", "allocation_pct"]]
                chart_df.columns = ["Channel", "Allocation %"]
                st.bar_chart(chart_df.set_index("Channel"))
