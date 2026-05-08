# MSC Cargo Brand Manager — Documentation

## Objective

The MSC Cargo Brand Manager is a single-pane-of-glass application for the MSC Cargo marketing team to monitor, analyze, and act on brand performance data. It replaces fragmented spreadsheet-based reporting with a real-time, AI-powered marketing studio built entirely on the Databricks Lakehouse platform.

### Business Goals

| Goal | How the App Delivers |
|------|---------------------|
| **Self-service analytics** | Natural language Q&A via Genie — no SQL required |
| **Real-time KPI monitoring** | Live dashboard pulling directly from the warehouse |
| **Faster decision-making** | AI-generated email drafts and campaign recommendations |
| **Proactive alerting** | Color-coded KPI cards flag breaches immediately |
| **Reduced analyst dependency** | Brand manager self-serves 80%+ of routine queries |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MSC Cargo Brand Manager                            │
│                       (Databricks App — Streamlit)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────┐  ┌──────────────┐  ┌────────────┐  ┌────────────────┐  │
│   │  KPI         │  │  Ask Genie   │  │   Email    │  │   Campaign     │  │
│   │  Dashboard   │  │  (NL Chat)   │  │  Composer  │  │   Planner      │  │
│   └──────┬───────┘  └──────┬───────┘  └─────┬──────┘  └───────┬────────┘  │
│          │                  │                 │                  │          │
└──────────┼──────────────────┼─────────────────┼──────────────────┼──────────┘
           │                  │                 │                  │
           ▼                  ▼                 ▼                  ▼
┌─────────────────┐  ┌───────────────┐  ┌──────────────┐  ┌──────────────┐
│  SQL Warehouse  │  │  Genie API    │  │  Foundation  │  │  SQL + LLM   │
│  (Direct SQL)   │  │  (Convers.)   │  │  Model API   │  │  (Combined)  │
└────────┬────────┘  └───────┬───────┘  └──────┬───────┘  └──────┬───────┘
         │                   │                  │                  │
         └───────────────────┴──────────────────┴──────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │     Databricks Lakehouse      │
                    │                               │
                    │  ┌─────────────────────────┐  │
                    │  │    Unity Catalog         │  │
                    │  │    (msc_cargo schema)    │  │
                    │  ├─────────────────────────┤  │
                    │  │  Dimensions    │  Facts  │  │
                    │  │  ─────────     │  ─────  │  │
                    │  │  dim_date      │  fact_  │  │
                    │  │  dim_region    │  brand_ │  │
                    │  │  dim_channel   │  aware  │  │
                    │  │  dim_campaign  │  ness   │  │
                    │  │               │  fact_  │  │
                    │  │               │  nps    │  │
                    │  │               │  ...    │  │
                    │  └─────────────────────────┘  │
                    │                               │
                    │  ┌─────────────────────────┐  │
                    │  │  Serverless SQL         │  │
                    │  │  Warehouse              │  │
                    │  └─────────────────────────┘  │
                    │                               │
                    │  ┌─────────────────────────┐  │
                    │  │  Genie Space            │  │
                    │  │  (NL → SQL → Results)   │  │
                    │  └─────────────────────────┘  │
                    │                               │
                    │  ┌─────────────────────────┐  │
                    │  │  Model Serving          │  │
                    │  │  (Claude Sonnet 4)      │  │
                    │  └─────────────────────────┘  │
                    └───────────────────────────────┘
```

### Component Breakdown

| Component | Role | Technology |
|-----------|------|------------|
| **Streamlit App** | Frontend UI and orchestration | Python, Streamlit, deployed as Databricks App |
| **SQL Warehouse** | Executes KPI queries and Genie-generated SQL | Databricks Serverless SQL |
| **Genie Space** | Natural language to SQL translation + conversational analytics | Databricks Genie (Conversation API) |
| **Foundation Model** | Email drafting and campaign recommendations | Claude Sonnet 4 via Model Serving |
| **Unity Catalog** | Data governance, access control, table storage | Delta Lake tables in `msc_cargo` schema |
| **Service Principal** | App-level authentication to all Databricks APIs | OAuth via `databricks-sdk` |

### Authentication Flow

```
User → Databricks App (OAuth login) → Streamlit App
                                          │
                                          ▼
                                    Service Principal
                                    (Config().authenticate())
                                          │
                        ┌─────────────────┼─────────────────┐
                        ▼                 ▼                  ▼
                  SQL Warehouse      Genie API        Model Serving
```

The app uses a **Service Principal** for all backend API calls. The SP is granted:
- `CAN_USE` on the SQL warehouse (via `app.yaml` resources)
- `CAN_QUERY` on the serving endpoint (via `app.yaml` resources)
- `CAN_RUN` on the Genie Space
- `SELECT` on all tables in `msc_cargo` schema

---

## Dataset

### Overview

The dataset models a B2B shipping/logistics brand management function for MSC Cargo. It covers a 12-month window (May 2024 – April 2025) split into:

- **Historical period:** May 2024 – October 2024
- **Current reporting period:** November 2024 – April 2025

All data is synthetic and designed to simulate realistic marketing KPI patterns for a global container shipping company.

### Star Schema

```
                          ┌──────────────┐
                          │   dim_date   │
                          │ ──────────── │
                          │ date_id (PK) │
                          │ month_name   │
                          │ quarter      │
                          │ is_current_  │
                          │   period     │
                          └──────┬───────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│ dim_region   │       │ dim_channel  │       │ dim_campaign │
│ ──────────── │       │ ──────────── │       │ ──────────── │
│ region_id    │       │ channel_id   │       │ campaign_id  │
│ region_name  │       │ channel_name │       │ campaign_name│
│ hq_city      │       │ channel_type │       │ budget_usd   │
│ headcount    │       │ audience     │       │ product_focus│
└──────┬───────┘       └──────┬───────┘       └──────┬───────┘
       │                      │                      │
       └──────────────────────┼──────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │   FACT TABLES     │
                    ├───────────────────┤
                    │ fact_brand_       │
                    │   awareness       │
                    │ fact_nps          │
                    │ fact_web_         │
                    │   performance     │
                    │ fact_campaign_    │
                    │   performance     │
                    │ fact_share_of_    │
                    │   voice           │
                    │ fact_email_       │
                    │   performance     │
                    │ fact_social_      │
                    │   performance     │
                    │ fact_brand_       │
                    │   compliance      │
                    └───────────────────┘
```

### Dimension Tables

| Table | Rows | Key Columns | Purpose |
|-------|------|-------------|---------|
| `dim_date` | 12 | `date_id`, `month_name`, `quarter`, `is_current_period` | Time dimension — one row per month |
| `dim_region` | 5 | `region_id`, `region_name`, `hq_city`, `headcount` | Geographic segmentation (EMEA, Americas, APAC, South Asia, MEA) |
| `dim_channel` | 9 | `channel_id`, `channel_name`, `channel_type`, `target_audience` | Marketing channels (owned/paid/earned) |
| `dim_campaign` | 7 | `campaign_id`, `campaign_name`, `budget_usd`, `product_focus`, `target_segment` | Campaign metadata with budget and targeting |

### Fact Tables

| Table | Rows | Grain | Key Metrics |
|-------|------|-------|-------------|
| `fact_brand_awareness` | 60 | Region × Month | `unaided_awareness_pct`, `aided_awareness_pct`, `preference_pct`, `purchase_intent_pct` |
| `fact_nps` | 60 | Region × Month | `nps_score`, `promoter_pct`, `detractor_pct`, `top_positive_driver`, `top_negative_driver` |
| `fact_web_performance` | 72 | Region × Channel × Month | `sessions`, `bounce_rate_pct`, `enquiry_conversion_pct`, `avg_session_duration_sec` |
| `fact_campaign_performance` | 21 | Campaign × Channel × Month | `impressions`, `clicks`, `mqls`, `roi_x`, `ctr_pct`, `spend_usd` |
| `fact_share_of_voice` | 60 | Competitor × Month | `share_of_voice_pct`, `sentiment_score`, `mention_count`, `competitor_name` |
| `fact_email_performance` | 12 | Campaign × Month | `sends`, `open_rate_pct`, `click_rate_pct`, `unsubscribe_rate_pct`, `revenue_influenced_usd` |
| `fact_social_performance` | 16 | Channel × Month | `followers`, `engagement_rate_pct`, `impressions`, `posts_published` |
| `fact_brand_compliance` | 15 | Region × Quarter | `overall_score_pct`, `visual_identity_score`, `messaging_score`, `digital_score` |

### Join Keys

All fact tables connect to dimensions via:
- `date_id` → `dim_date.date_id` (YYYYMM integer, e.g., 202411)
- `region_id` → `dim_region.region_id`
- `channel_id` → `dim_channel.channel_id`
- `campaign_id` → `dim_campaign.campaign_id`

---

## Application Pages

### 1. Home — KPI Dashboard

Displays 9 key brand metrics as cards with color-coded status indicators:

| KPI | Target | Alert Threshold | Source Table |
|-----|--------|-----------------|--------------|
| Unaided Brand Awareness | 65% | < 50% | `fact_brand_awareness` |
| NPS Score | 35 | < 25 | `fact_nps` |
| Web Enquiry Conversion | 2.5% | < 1.8% | `fact_web_performance` |
| Campaign ROI | 3.5x | < 2.5x | `fact_campaign_performance` |
| MQLs per Month | 650 | < 500 | `fact_campaign_performance` |
| Share of Voice | 27% | < 20% | `fact_share_of_voice` |
| Brand Compliance | 90% | < 80% | `fact_brand_compliance` |
| Email Open Rate | 26% | < 20% | `fact_email_performance` |
| LinkedIn Engagement | 2.5% | < 1.8% | `fact_social_performance` |

Card colors: **Blue** = on target, **Gold** = warning, **Red** = alert.

The home page also shows:
- **Recent campaigns** — Latest campaigns from `dim_campaign` with budgets
- **Top performers by channel** — Channel ROI rankings from `fact_campaign_performance`

### 2. Ask Genie — Natural Language Analytics

A conversational interface powered by the Databricks Genie Space. The user types a question in natural language, and the system:

1. Sends the question to the Genie Conversation API
2. Genie translates it to SQL using table schemas and instructions
3. SQL executes on the serverless warehouse
4. Results return as a data table with auto-generated charts
5. Conversation context is maintained for follow-up questions

**Example questions:**
- "Why is NPS so low in South Asia?"
- "Which campaign had the best ROI and why?"
- "Show me share of voice trend vs Maersk over the last 6 months"

### 3. Email Composer — AI-Powered Communications

Generates professional, data-driven emails using Claude Sonnet 4. The user provides:
- Recipient, subject, and tone (professional/urgent/congratulatory/executive-summary)
- Context with KPI data or Genie insights

The LLM generates a formatted email draft using shipping/logistics industry terminology.

### 4. Campaign Planner — AI Budget Recommendations

Helps plan new campaigns by:
1. Querying historical campaign performance data by channel
2. Accepting campaign parameters (budget, segment, product, duration)
3. Using Claude Sonnet 4 to recommend optimal channel budget allocation
4. Displaying recommendations with expected ROI per channel

---

## Deployment

### Infrastructure

| Resource | Value |
|----------|-------|
| Workspace | `fevm-serverless-stable-3n0ihb.cloud.databricks.com` |
| Catalog | `serverless_stable_3n0ihb_catalog` |
| Schema | `msc_cargo` |
| SQL Warehouse | Serverless (`b868e84cedeb4262`) |
| Genie Space | `01f14acf90d51d9aadeaff3820a01f5b` |
| LLM Endpoint | `databricks-claude-sonnet-4` |
| App URL | `https://msc-cargo-brand-mgr-st-7474645572615955.aws.databricksapps.com` |

### Setup Steps

1. **Create schema and upload data:**
   ```sql
   CREATE SCHEMA IF NOT EXISTS <catalog>.msc_cargo;
   CREATE VOLUME IF NOT EXISTS <catalog>.msc_cargo.msc_cargo_raw;
   ```
   Upload all CSVs from `dataset/` to the volume.

2. **Create tables** using `dataset/databricks_ddl.sql`.

3. **Create Genie Space** with the 12 tables and instructions from `dataset/GENIE_SPACE_INSTRUCTIONS.md`.

4. **Deploy the Streamlit app** as a Databricks App with the configuration in `streamlit_app/app.yaml`.

### app.yaml Configuration

```yaml
command:
  - streamlit
  - run
  - app.py
  - --server.port=8000
  - --server.address=0.0.0.0

env:
  - name: DATABRICKS_HOST
    value: "https://<workspace>.cloud.databricks.com"
  - name: GENIE_SPACE_ID
    value: "<genie-space-id>"
  - name: WAREHOUSE_ID
    value: "<warehouse-id>"
  - name: CATALOG
    value: "<catalog-name>"
  - name: SCHEMA
    value: "msc_cargo"
  - name: LLM_ENDPOINT
    value: "databricks-claude-sonnet-4"

resources:
  - name: sql-warehouse
    sql_warehouse:
      id: <warehouse-id>
      permission: CAN_USE
  - name: serving-endpoint
    serving_endpoint:
      name: databricks-claude-sonnet-4
      permission: CAN_QUERY
```

The `resources` section automatically grants the app's Service Principal the required permissions at deploy time.

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Streamlit over React** | Faster iteration, native Python data handling, built-in chart support |
| **Service Principal auth** | No OBO token available in Databricks Apps; SP provides stable, scoped access |
| **Genie + direct SQL fallback** | Genie query-result API can fail for SP; direct SQL execution ensures data always displays |
| **Serverless warehouse** | No cluster management, instant startup, cost-efficient for sporadic queries |
| **Star schema** | Clean dimensional model optimized for Genie's SQL generation and dashboard queries |
| **Dark mode UI** | Matches Databricks native theme; professional appearance for executive users |
