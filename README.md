# MSC Cargo Brand Manager — Genie Space

An AI-powered analytics assistant for the MSC Cargo brand management team, built on Databricks Genie. It enables natural-language exploration of marketing KPIs across brand awareness, NPS, campaign performance, digital channels, and competitive positioning.

## Project Objectives

1. **Self-service analytics** — Give the MSC Cargo brand manager instant answers to performance questions without writing SQL or waiting for analyst support.
2. **Proactive alerting** — Surface KPIs that are below target or declining, with structured root-cause hypotheses.
3. **Actionable recommendations** — Every insight comes with 2–3 concrete next steps the brand manager can take.
4. **Cross-functional visibility** — Unify brand, digital, campaign, and competitive data into a single conversational interface.

## Business Outcomes

| Outcome | Metric |
|---------|--------|
| Faster time-to-insight | Minutes instead of days for ad-hoc marketing questions |
| Reduced analyst dependency | Brand manager self-serves 80%+ of routine queries |
| Earlier issue detection | KPI breaches flagged as soon as data refreshes |
| Improved campaign ROI | Data-driven reallocation based on channel/region performance |
| Brand consistency | Compliance gaps identified and tracked per region |

## Dataset

The dataset covers a 12-month window (May 2024 – April 2025) split into:
- **Historical period:** May 2024 – October 2024
- **Current reporting period:** November 2024 – April 2025

### Dimension Tables

| Table | Rows | Description |
|-------|------|-------------|
| `dim_date` | 12 | Calendar dimension — month, quarter, period label, `is_current_period` flag |
| `dim_region` | 5 | Global regions (EMEA, Americas, APAC, South Asia, MEA) with office/headcount data |
| `dim_channel` | 9 | Marketing channels (owned, paid, earned) with audience segments |
| `dim_campaign` | 7 | Campaign metadata — budget, dates, product focus, target segment |

### Fact Tables

| Table | Rows | Description |
|-------|------|-------------|
| `fact_brand_awareness` | 60 | Monthly unaided/aided awareness, preference, and purchase intent by region |
| `fact_nps` | 60 | Monthly NPS with promoter/passive/detractor split and top drivers |
| `fact_web_performance` | 72 | Web sessions, bounce rate, enquiry conversion by region and channel |
| `fact_campaign_performance` | 21 | Impression-to-ROI funnel per campaign, channel, and month |
| `fact_share_of_voice` | 60 | Monthly share of voice and sentiment vs Maersk, CMA CGM, Hapag-Lloyd |
| `fact_email_performance` | 12 | Email send/open/click/unsubscribe and revenue influence by campaign |
| `fact_social_performance` | 16 | LinkedIn and YouTube followers, engagement, impressions |
| `fact_brand_compliance` | 15 | Quarterly compliance audit scores by region |

### Key Relationships

- All fact tables join to `dim_date` on `date_id` (YYYYMM integer)
- Regional facts join to `dim_region` on `region_id`
- Channel-level facts join to `dim_channel` on `channel_id`
- Campaign facts join to `dim_campaign` on `campaign_id`

## KPI Targets

| KPI | Target | Alert Threshold |
|-----|--------|-----------------|
| Unaided brand awareness | 65% globally | < 50% in any region |
| NPS | 35 globally | < 25 in any region |
| Web enquiry conversion | 2.5% | < 1.8% |
| Campaign ROI | 3.5x | < 2.5x |
| MQLs per month | 650 | < 500 |
| Share of voice | 27% | < 20% |
| Brand compliance | 90% | < 80% in any region |
| Email open rate | 26% | < 20% |
| LinkedIn engagement rate | 2.5% | < 1.8% |

## Deployment

### Prerequisites

- Databricks workspace with Unity Catalog enabled
- SQL warehouse (serverless recommended)

### Setup Steps

1. **Create schema and volume:**
   ```sql
   CREATE SCHEMA IF NOT EXISTS <catalog>.msc_cargo;
   CREATE VOLUME IF NOT EXISTS <catalog>.msc_cargo.msc_cargo_raw;
   ```

2. **Upload CSV files** from the `dataset/` folder to the volume.

3. **Create tables** using `dataset/databricks_ddl.sql` (update `<catalog>` placeholder).

4. **Create Genie Space** using the `manage_genie` MCP tool or the Databricks UI with the instructions in `dataset/GENIE_SPACE_INSTRUCTIONS.md`.

5. **Grant permissions** to target users:
   ```bash
   databricks api patch /api/2.0/permissions/genie/$SPACE_ID \
     --json '{"access_control_list": [{"group_name": "users", "permission_level": "CAN_RUN"}]}'
   ```

### Current Deployment

- **Workspace:** `fevm-serverless-stable-3n0ihb.cloud.databricks.com`
- **Catalog:** `serverless_stable_3n0ihb_catalog`
- **Schema:** `msc_cargo`
- **Genie Space ID:** `01f14acf90d51d9aadeaff3820a01f5b`
- **Access:** All workspace users (CAN_RUN)

## Example Questions

- "Why is NPS so low in South Asia and MEA?"
- "Which campaign had the worst ROI and what drove that?"
- "How is our share of voice trending vs Maersk?"
- "What are the top reasons for poor web conversion in South Asia?"
- "Show me all months where we missed the MQL target"
- "Which region is furthest from brand awareness target?"
- "Compare email performance across all campaigns"
