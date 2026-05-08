import os


class Settings:
    DATABRICKS_HOST: str = os.getenv("DATABRICKS_HOST", "")
    GENIE_SPACE_ID: str = os.getenv("GENIE_SPACE_ID", "")
    WAREHOUSE_ID: str = os.getenv("WAREHOUSE_ID", "")
    CATALOG: str = os.getenv("CATALOG", "serverless_stable_3n0ihb_catalog")
    SCHEMA: str = os.getenv("SCHEMA", "msc_cargo")
    LLM_ENDPOINT: str = os.getenv("LLM_ENDPOINT", "databricks-claude-sonnet-4")
    API_PREFIX: str = "/api"


settings = Settings()
