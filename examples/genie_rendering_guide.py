"""
Genie Response Rendering — Developer Guide
============================================

This file demonstrates the common pitfalls when integrating the Databricks Genie
Conversation API into a Streamlit app, and how to solve them.

The Genie API is ASYNCHRONOUS and returns SQL + metadata, but getting the actual
DATA ROWS requires extra steps that are easy to miss.

Run this example:
    streamlit run examples/genie_rendering_guide.py
"""

import os
import time
import requests
import streamlit as st
import pandas as pd
from databricks.sdk.core import Config

st.set_page_config(page_title="Genie Rendering Guide", layout="wide")

DATABRICKS_HOST = os.getenv("DATABRICKS_HOST", "")
GENIE_SPACE_ID = os.getenv("GENIE_SPACE_ID", "")
WAREHOUSE_ID = os.getenv("WAREHOUSE_ID", "")


def get_auth():
    cfg = Config()
    host = DATABRICKS_HOST or cfg.host
    if host and not host.startswith("http"):
        host = f"https://{host}"
    return host, cfg.authenticate()


# =============================================================================
# ❌ BROKEN EXAMPLE — What most developers try first
# =============================================================================

st.header("❌ Broken Example — Common Mistakes")
st.markdown("""
Most developers hit these 3 problems when integrating Genie:

1. **Only showing SQL text** — Genie returns the generated SQL, but not the data rows
2. **Race condition** — Polling too early or treating intermediate statuses as terminal
3. **"No response" when data exists** — Displaying error text even when the table rendered
""")

with st.expander("Show broken code", expanded=True):
    st.code('''
def ask_genie_BROKEN(question: str) -> dict:
    """❌ BROKEN — This is what most developers try first."""
    host, headers = get_auth()
    base = f"{host}/api/2.0/genie/spaces/{GENIE_SPACE_ID}"

    # Start conversation
    resp = requests.post(
        f"{base}/start-conversation",
        headers=headers, json={"content": question},
    )
    data = resp.json()
    conversation_id = data.get("conversation_id")
    msg_id = data.get("message_id")

    # ❌ BUG #1: Polling immediately without initial wait
    # Genie needs 2-3 seconds to even begin processing
    for _ in range(30):
        poll = requests.get(
            f"{base}/conversations/{conversation_id}/messages/{msg_id}",
            headers=headers,
        )
        msg = poll.json()
        status = msg.get("status", "")

        # ❌ BUG #2: Missing statuses — "SUBMITTED" and "" are NOT terminal!
        # This treats them as complete, returning empty results
        if status not in ("EXECUTING_QUERY", "FETCHING_METADATA", "ASKING_AI"):
            # ❌ BUG #3: Only extracting SQL text, never fetching actual data rows
            for att in msg.get("attachments", []):
                query = att.get("query")
                if query:
                    return {
                        "sql": query.get("query"),
                        "text": query.get("description"),
                        # ← No columns! No data! Just SQL text!
                    }
            return {"text": msg.get("content", "No response")}
        time.sleep(1.5)

    return {"error": "Timeout"}


def display_BROKEN(result: dict):
    """❌ BROKEN — Only shows text, never renders tables or charts."""
    # Shows "No response" even when data was successfully retrieved
    content = result.get("text") or result.get("error") or "No response"
    st.markdown(content)

    # Developer sees SQL in the response and just displays it as text
    if result.get("sql"):
        st.code(result["sql"], language="sql")
    # ← No table! No chart! User just sees raw SQL.
''', language="python")

st.markdown("""
**What the user sees with broken code:**
- "No response" message (race condition — polled too early)
- Or just the SQL query as text (no data table, no visualization)
- Or intermittent failures ("works if I wait, fails on first try")
""")

st.divider()

# =============================================================================
# ✅ WORKING EXAMPLE — The correct approach
# =============================================================================

st.header("✅ Working Example — Correct Implementation")
st.markdown("""
The fix requires solving 3 problems:
1. **Wait before polling** + include ALL non-terminal statuses
2. **Fetch query-result** from the attachment endpoint to get data rows
3. **Fallback to direct SQL** when query-result fails (common with Service Principals)
""")

with st.expander("Show working code", expanded=True):
    st.code('''
def execute_sql_with_columns(sql: str) -> tuple[list, list]:
    """Execute SQL directly and return (columns, data_array).
    Used as fallback when Genie query-result endpoint fails."""
    host, headers = get_auth()
    resp = requests.post(
        f"{host}/api/2.0/sql/statements",
        headers=headers,
        json={"warehouse_id": WAREHOUSE_ID, "statement": sql, "wait_timeout": "30s"},
    )
    if resp.status_code >= 400:
        return [], []
    result = resp.json()
    if result.get("status", {}).get("state") == "FAILED":
        return [], []
    columns = [c.get("name", "") for c in result.get("manifest", {}).get("schema", {}).get("columns", [])]
    data = result.get("result", {}).get("data_array", [])
    return columns, data


def ask_genie_CORRECT(question: str, conversation_id: str | None = None) -> dict:
    """✅ CORRECT — Handles all edge cases."""
    host, headers = get_auth()
    base = f"{host}/api/2.0/genie/spaces/{GENIE_SPACE_ID}"

    # Start or continue conversation
    if conversation_id:
        resp = requests.post(
            f"{base}/conversations/{conversation_id}/messages",
            headers=headers, json={"content": question},
        )
        data = resp.json()
        msg_id = data.get("message_id") or data.get("id")
    else:
        resp = requests.post(
            f"{base}/start-conversation",
            headers=headers, json={"content": question},
        )
        data = resp.json()
        conversation_id = data.get("conversation_id")
        msg_id = data.get("message_id")

    if not conversation_id or not msg_id:
        return {"status": "FAILED", "error": "Missing IDs"}

    # ✅ FIX #1: Include ALL non-terminal statuses + initial delay
    PENDING_STATUSES = {
        "EXECUTING_QUERY", "FETCHING_METADATA", "ASKING_AI",
        "SUBMITTED", "FILTERING", "PENDING", ""  # ← These are often missed!
    }
    time.sleep(2)  # ← Critical: Genie needs time to start processing

    for _ in range(80):  # Up to ~160 seconds total
        poll = requests.get(
            f"{base}/conversations/{conversation_id}/messages/{msg_id}",
            headers=headers,
        )
        if poll.status_code >= 400:
            time.sleep(2)
            continue

        msg = poll.json()
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

                    # ✅ FIX #2: Fetch actual data rows from query-result endpoint
                    att_id = att.get("id")
                    if status == "COMPLETED" and att_id:
                        qr_resp = requests.get(
                            f"{base}/conversations/{conversation_id}/messages/{msg_id}/query-result/{att_id}",
                            headers=headers,
                        )
                        if qr_resp.status_code < 400:
                            qr = qr_resp.json()
                            stmt = qr.get("statement_response", {})
                            cols = [c.get("name", "") for c in
                                    stmt.get("manifest", {}).get("schema", {}).get("columns", [])]
                            data_rows = stmt.get("result", {}).get("data_array", [])
                            if cols and data_rows:
                                result["columns"] = cols
                                result["data"] = data_rows

                # Also check for text attachments
                text_att = att.get("text")
                if text_att:
                    if isinstance(text_att, dict):
                        result["text_response"] = text_att.get("content", "")
                    elif isinstance(text_att, str):
                        result["text_response"] = text_att

            # ✅ FIX #3: Fallback — execute SQL directly if query-result failed
            if result["sql"] and not result["data"]:
                cols, rows = execute_sql_with_columns(result["sql"])
                if cols and rows:
                    result["columns"] = cols
                    result["data"] = rows

            return result
        time.sleep(2)

    return {"status": "TIMEOUT", "error": "Timed out", "conversation_id": conversation_id}


def display_genie_result(result: dict):
    """✅ CORRECT — Renders text, table, and auto-chart."""
    text = result.get("text_response")
    error = result.get("error")
    has_data = result.get("data") and result.get("columns")

    # ✅ FIX #4: Don't show "No response" when data exists
    if text:
        st.markdown(text)
    elif error:
        st.error(error)
    elif not has_data:
        st.warning("No response")

    # Render data table
    if has_data:
        df = pd.DataFrame(result["data"], columns=result["columns"])
        # Convert numeric columns (Genie returns everything as strings)
        for col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col])
            except (ValueError, TypeError):
                pass

        st.dataframe(df, use_container_width=True, hide_index=True)

        # Auto-generate chart if we have a label column + numeric columns
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        non_numeric_cols = [c for c in df.columns if c not in numeric_cols]

        if numeric_cols and non_numeric_cols and len(df) > 1:
            label_col = non_numeric_cols[0]
            chart_df = df.set_index(label_col)[numeric_cols]
            if len(df) <= 20:
                st.bar_chart(chart_df)
            else:
                st.line_chart(chart_df)

    # Show SQL in collapsible section
    if result.get("sql"):
        with st.expander("View SQL Query"):
            st.code(result["sql"], language="sql")
''', language="python")

st.divider()

# =============================================================================
# KEY LESSONS
# =============================================================================

st.header("Key Lessons")

st.markdown("""
### 1. The Genie API is asynchronous — you MUST poll

```
POST /start-conversation → returns conversation_id + message_id
GET  /messages/{msg_id}  → poll until status is terminal
GET  /query-result/{att_id} → fetch actual data rows
```

The message goes through these statuses:
```
"" → SUBMITTED → PENDING → ASKING_AI → FETCHING_METADATA → EXECUTING_QUERY → COMPLETED
```

**All statuses before COMPLETED are non-terminal.** If you treat `SUBMITTED` or `""` as
terminal, you'll get empty responses on fast queries.

### 2. The query-result endpoint is separate

Genie's message response contains:
- `attachments[].query.query` → the SQL text
- `attachments[].query.description` → text explanation
- `attachments[].id` → attachment ID needed to fetch data

You must call `/query-result/{attachment_id}` to get the actual rows.
This endpoint sometimes fails for Service Principals — always have a fallback.

### 3. Always have a direct SQL fallback

```python
if result["sql"] and not result["data"]:
    # query-result failed — execute the SQL ourselves
    cols, rows = execute_sql_with_columns(result["sql"])
```

This guarantees users see data even when the query-result API returns 403/500.

### 4. Don't show "No response" when data exists

Genie often returns data tables without a text description. Your display function
should check for data BEFORE deciding to show error text:

```python
# ❌ Wrong
content = result.get("text_response") or "No response"
st.markdown(content)  # Shows "No response" above a perfectly good table

# ✅ Right
if text:
    st.markdown(text)
elif not has_data:
    st.warning("No response")
# If has_data is True, just show the table — no text needed
```

### 5. Convert string columns to numeric

Genie returns ALL values as strings in `data_array`. If you don't convert:
- Charts won't render (Streamlit needs numeric types)
- Sorting is alphabetical ("9" > "10")
- Aggregations fail

```python
for col in df.columns:
    try:
        df[col] = pd.to_numeric(df[col])
    except (ValueError, TypeError):
        pass
```
""")
