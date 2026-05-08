-- Run this in a Databricks SQL notebook to create tables from uploaded CSVs.
-- Assumes CSVs are uploaded to a Unity Catalog volume at:
--   /Volumes/<catalog>/<schema>/msc_cargo_raw/

CREATE SCHEMA IF NOT EXISTS msc_cargo;

CREATE OR REPLACE TABLE msc_cargo.dim_date
  USING CSV OPTIONS (header 'true', inferSchema 'true')
  LOCATION '/Volumes/<catalog>/msc_cargo/msc_cargo_raw/dim_date.csv';

CREATE OR REPLACE TABLE msc_cargo.dim_region
  USING CSV OPTIONS (header 'true', inferSchema 'true')
  LOCATION '/Volumes/<catalog>/msc_cargo/msc_cargo_raw/dim_region.csv';

CREATE OR REPLACE TABLE msc_cargo.dim_channel
  USING CSV OPTIONS (header 'true', inferSchema 'true')
  LOCATION '/Volumes/<catalog>/msc_cargo/msc_cargo_raw/dim_channel.csv';

CREATE OR REPLACE TABLE msc_cargo.dim_campaign
  USING CSV OPTIONS (header 'true', inferSchema 'true')
  LOCATION '/Volumes/<catalog>/msc_cargo/msc_cargo_raw/dim_campaign.csv';

CREATE OR REPLACE TABLE msc_cargo.fact_brand_awareness
  USING CSV OPTIONS (header 'true', inferSchema 'true')
  LOCATION '/Volumes/<catalog>/msc_cargo/msc_cargo_raw/fact_brand_awareness.csv';

CREATE OR REPLACE TABLE msc_cargo.fact_nps
  USING CSV OPTIONS (header 'true', inferSchema 'true')
  LOCATION '/Volumes/<catalog>/msc_cargo/msc_cargo_raw/fact_nps.csv';

CREATE OR REPLACE TABLE msc_cargo.fact_web_performance
  USING CSV OPTIONS (header 'true', inferSchema 'true')
  LOCATION '/Volumes/<catalog>/msc_cargo/msc_cargo_raw/fact_web_performance.csv';

CREATE OR REPLACE TABLE msc_cargo.fact_campaign_performance
  USING CSV OPTIONS (header 'true', inferSchema 'true')
  LOCATION '/Volumes/<catalog>/msc_cargo/msc_cargo_raw/fact_campaign_performance.csv';

CREATE OR REPLACE TABLE msc_cargo.fact_share_of_voice
  USING CSV OPTIONS (header 'true', inferSchema 'true')
  LOCATION '/Volumes/<catalog>/msc_cargo/msc_cargo_raw/fact_share_of_voice.csv';

CREATE OR REPLACE TABLE msc_cargo.fact_email_performance
  USING CSV OPTIONS (header 'true', inferSchema 'true')
  LOCATION '/Volumes/<catalog>/msc_cargo/msc_cargo_raw/fact_email_performance.csv';

CREATE OR REPLACE TABLE msc_cargo.fact_social_performance
  USING CSV OPTIONS (header 'true', inferSchema 'true')
  LOCATION '/Volumes/<catalog>/msc_cargo/msc_cargo_raw/fact_social_performance.csv';

CREATE OR REPLACE TABLE msc_cargo.fact_brand_compliance
  USING CSV OPTIONS (header 'true', inferSchema 'true')
  LOCATION '/Volumes/<catalog>/msc_cargo/msc_cargo_raw/fact_brand_compliance.csv';

-- Verify row counts
SELECT 'dim_date' as tbl, count(*) as rows FROM msc_cargo.dim_date
UNION ALL SELECT 'dim_region', count(*) FROM msc_cargo.dim_region
UNION ALL SELECT 'dim_channel', count(*) FROM msc_cargo.dim_channel
UNION ALL SELECT 'dim_campaign', count(*) FROM msc_cargo.dim_campaign
UNION ALL SELECT 'fact_brand_awareness', count(*) FROM msc_cargo.fact_brand_awareness
UNION ALL SELECT 'fact_nps', count(*) FROM msc_cargo.fact_nps
UNION ALL SELECT 'fact_web_performance', count(*) FROM msc_cargo.fact_web_performance
UNION ALL SELECT 'fact_campaign_performance', count(*) FROM msc_cargo.fact_campaign_performance
UNION ALL SELECT 'fact_share_of_voice', count(*) FROM msc_cargo.fact_share_of_voice
UNION ALL SELECT 'fact_email_performance', count(*) FROM msc_cargo.fact_email_performance
UNION ALL SELECT 'fact_social_performance', count(*) FROM msc_cargo.fact_social_performance
UNION ALL SELECT 'fact_brand_compliance', count(*) FROM msc_cargo.fact_brand_compliance;
