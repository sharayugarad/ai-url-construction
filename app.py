"""
app.py — Streamlit UI for Facebook ad-export URL construction.

Workflow
--------
1. App loads credentials from LOCAL_ENV_PATH (required for Zoho tab).
2. User either:
   a. Uploads a CSV/Excel with Lead IDs (fetches attachments from Zoho CRM), OR
   b. Uploads a ZIP file containing Facebook HTML exports (processed locally).
3. App extracts Facebook HTML exports, parses them, constructs URLs, and shows results.
4. User downloads results as Excel.

Configuration
-------------
Set LOCAL_ENV_PATH to the absolute path of your local.env file.
The file uses Python-style key = value syntax, e.g.:

    API_DOMAIN = "https://www.zohoapis.com"
    API_VERSION = "v7"
    MODULE_API_NAME = "Leads"
    CLIENT_ID = ""
    CLIENT_SECRET = ""
    REFRESH_TOKEN = ""
    TOKEN_URL = "https://accounts.zoho.com/oauth/v2/token"
    OPENAI_API_KEY =
    VERIFY_URLS = false
    CACHE_PATH = url_cache.json
"""

from __future__ import annotations

import io
import logging
from typing import Optional
from urllib.parse import urlparse

import pandas as pd
import streamlit as st

from fb_parser import parse_html_content
from zoho_downloader import ZohoDownloader, ZohoAuthError, walk_zip
from url_constructor import URLConstructor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# local.env path — set this before running
# ---------------------------------------------------------------------------
LOCAL_ENV_PATH = r'/Users/sharayu/CodeLab/Local Secrets/secrets.local.env'

# ---------------------------------------------------------------------------
# local.env loader
# ---------------------------------------------------------------------------

def load_local_env(path: str) -> dict[str, str]:
    """
    Parse a Python-style key = value env file into a plain string dict.

    Handles:
    - Quoted values:  KEY = "value"  or  KEY = 'value'
    - Python None:    KEY = None   → empty string
    - Empty values:   KEY =        → empty string
    - Comments:       # this line is ignored
    """
    env: dict[str, str] = {}
    if not path:
        return env
    try:
        with open(path, encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                # Strip surrounding quotes
                if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
                    value = value[1:-1]
                # Treat Python None / null as empty
                if value.lower() in ("none", "null"):
                    value = ""
                env[key] = value
    except FileNotFoundError:
        logger.warning("local.env not found at %r — using defaults", path)
    except Exception as exc:
        logger.warning("Could not read local.env: %s", exc)
    return env


def _accounts_domain_from_token_url(token_url: str) -> str:
    """
    Derive the Zoho accounts base URL from a full token URL.

    e.g. "https://accounts.zoho.com/oauth/v2/token" → "https://accounts.zoho.com"
    """
    if not token_url:
        return "https://accounts.zoho.com"
    parsed = urlparse(token_url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return "https://accounts.zoho.com"


# Load env at module level
_env = load_local_env(LOCAL_ENV_PATH)

# ---------------------------------------------------------------------------
# All configuration sourced from local.env — nothing exposed in the UI
# ---------------------------------------------------------------------------
api_domain      = _env.get("ZOHO_CRM_API_BASE", _env.get("API_DOMAIN", "https://www.zohoapis.com"))
accounts_domain = _env.get("ZOHO_CRM_ACCOUNTS_BASE", _accounts_domain_from_token_url(_env.get("TOKEN_URL", "")))
client_id       = _env.get("ZOHO_CRM_CLIENT_ID", _env.get("CLIENT_ID", ""))
client_secret   = _env.get("ZOHO_CRM_CLIENT_SECRET", _env.get("CLIENT_SECRET", ""))
refresh_token   = _env.get("ZOHO_CRM_REFRESH_TOKEN", _env.get("REFRESH_TOKEN", ""))
zoho_module     = _env.get("MODULE_API_NAME", "Leads")
openai_key      = _env.get("OPENAI_API_KEY", "")
verify_urls     = _env.get("VERIFY_URLS", "false").lower() == "true"
cache_path      = _env.get("CACHE_PATH", "url_cache.json")
_api_version    = _env.get("API_VERSION", "v7")

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="FB Ad Export → URL Constructor",
    page_icon="🔗",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_downloader() -> Optional[ZohoDownloader]:
    if not all([client_id, client_secret, refresh_token]):
        return None
    return ZohoDownloader(
        api_domain=api_domain,
        accounts_domain=accounts_domain,
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        module=zoho_module,
        api_version=_api_version,
    )


def _build_constructor() -> URLConstructor:
    return URLConstructor(
        openai_api_key=openai_key,
        cache_path=cache_path,
        verify_urls=verify_urls,
    )


def _read_lead_ids_from_upload(file_obj) -> list[str]:
    """Extract Lead IDs from an uploaded CSV or Excel file."""
    name = file_obj.name.lower()
    if name.endswith(".csv"):
        df = pd.read_csv(file_obj, dtype=str)
    else:
        df = pd.read_excel(file_obj, dtype=str)

    # Find a column that looks like it contains IDs
    id_col = None
    for col in df.columns:
        if col.strip().lower() in ("lead id", "leadid", "id", "record id", "recordid"):
            id_col = col
            break
    if id_col is None:
        # Fall back to first column
        id_col = df.columns[0]
        st.warning(f"Could not find a 'Lead ID' column — using first column: {id_col!r}")

    ids = df[id_col].dropna().astype(str).str.strip()
    # Zoho REST API requires numeric IDs; strip the "zcrm_" prefix if present
    ids = ids.str.replace(r"^zcrm_", "", regex=True)
    return ids.tolist()


def process_records(
    lead_ids: list[str],
    downloader: ZohoDownloader,
    constructor: URLConstructor,
    progress_cb,
    status_cb,
) -> pd.DataFrame:
    """
    Core processing pipeline.

    Parameters
    ----------
    lead_ids : list[str]
        Zoho CRM record IDs to process.
    downloader : ZohoDownloader
    constructor : URLConstructor
    progress_cb : callable(float)
        Updates a progress bar (0.0 – 1.0).
    status_cb : callable(str)
        Emits a status message.

    Returns
    -------
    pd.DataFrame with columns:
        Lead ID, Filename, Generated By, Keywords Scraped,
        Constructed URL, Confidence[, URL Verified]
    """
    total = len(lead_ids)

    # Phase 1: Fetch and parse all HTML from Zoho (no URL construction yet)
    # Each entry: (record_id, display_path, generated_by, targets)
    # display_path="" signals a record with no attachments
    parsed_data: list[tuple[str, str, str, list[str]]] = []

    for idx, record_id in enumerate(lead_ids):
        status_cb(f"[{idx+1}/{total}] Fetching attachments for record {record_id}…")
        try:
            html_files = downloader.collect_html_from_record(record_id)
        except ZohoAuthError as exc:
            st.error(f"Zoho auth error on record {record_id}: {exc}")
            parsed_data.append((record_id, "", "", []))
            progress_cb((idx + 1) / total)
            continue
        except Exception as exc:
            st.warning(f"Skipping record {record_id}: {exc}")
            parsed_data.append((record_id, "", "", []))
            progress_cb((idx + 1) / total)
            continue

        if not html_files:
            parsed_data.append((record_id, "", "", []))
        else:
            for display_path, html_text in html_files:
                filename = display_path.split("/")[-1]
                status_cb(f"[{idx+1}/{total}] Parsing {filename}…")
                parsed = parse_html_content(display_path, html_text)
                if parsed is None:
                    continue
                generated_by = parsed["generated_by"]
                keywords = parsed["keywords"]
                targets = keywords if keywords else ([generated_by] if generated_by else [""])
                parsed_data.append((record_id, display_path, generated_by, targets))

        progress_cb((idx + 1) / total)

    # Phase 2: Batch URL construction — single LLM call for all unique names
    all_names = [kw or gb or "" for (_, _, gb, tgts) in parsed_data for kw in tgts]
    unique_names = list(dict.fromkeys(n for n in all_names if n))
    status_cb(f"Constructing URLs for {len(unique_names)} unique name(s)…")
    url_map = constructor.batch_construct(unique_names)

    # Phase 3: Build result rows
    rows: list[dict] = []
    for record_id, display_path, generated_by, targets in parsed_data:
        if not display_path:
            rows.append(
                {
                    "Lead ID": record_id,
                    "Filename": "",
                    "Generated By": "",
                    "Keywords Scraped": "",
                    "Constructed URL": "",
                    "Confidence": "UNKNOWN",
                    **({} if not verify_urls else {"URL Verified": False}),
                }
            )
            continue

        for keyword in targets:
            company_name = keyword or generated_by or ""
            url, confidence = url_map.get(company_name, ("", "UNKNOWN")) if company_name else ("", "UNKNOWN")
            row = {
                "Lead ID": record_id,
                "Filename": display_path,
                "Generated By": generated_by,
                "Keywords Scraped": keyword,
                "Constructed URL": url,
                "Confidence": confidence,
            }
            if verify_urls:
                cached = constructor._cache.get(constructor._cache_key(company_name), {})
                row["URL Verified"] = cached.get("verified", False)
            rows.append(row)

    cols = [
        "Lead ID", "Filename", "Generated By", "Keywords Scraped", "Constructed URL", "Confidence",
    ] + (["URL Verified"] if verify_urls else [])
    return pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Serialize DataFrame to Excel bytes."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Results")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Main UI
# ---------------------------------------------------------------------------

st.title("🔗 Facebook Ad Export → URL Constructor")
st.caption(
    "Downloads Zoho CRM attachments, extracts Facebook HTML exports, "
    "and constructs advertiser website URLs."
)

creds_ok = all([client_id, client_secret, refresh_token])
if not creds_ok:
    st.error(
        "Zoho CRM credentials are missing. "
        f"Set CLIENT_ID, CLIENT_SECRET, and REFRESH_TOKEN in your local.env file (`{LOCAL_ENV_PATH}`)."
    )

tab_upload, tab_zip = st.tabs(["📂 Upload CSV/Excel", "📦 Upload ZIP File"])

# ---------------------------------------------------------------------------
# Tab 1 — Upload CSV/Excel
# ---------------------------------------------------------------------------
with tab_upload:
    st.subheader("Upload a CSV or Excel file containing Lead IDs")
    uploaded = st.file_uploader(
        "Choose file",
        type=["csv", "xlsx", "xls"],
        help="File must contain a column named 'Lead ID', 'id', or similar.",
    )

    if uploaded and creds_ok:
        lead_ids = _read_lead_ids_from_upload(uploaded)
        st.info(f"Found **{len(lead_ids)}** Lead ID(s) in uploaded file.")

        if st.button("▶ Process uploaded Lead IDs", key="btn_upload"):
            downloader = _build_downloader()
            constructor = _build_constructor()

            progress_bar = st.progress(0.0)
            status_text = st.empty()

            with st.status("Processing…", expanded=True) as status_widget:
                try:
                    df_results = process_records(
                        lead_ids=lead_ids,
                        downloader=downloader,
                        constructor=constructor,
                        progress_cb=lambda v: progress_bar.progress(v),
                        status_cb=lambda msg: (
                            status_text.text(msg),
                            st.write(msg),
                        ),
                    )
                    status_widget.update(label="Done!", state="complete")
                except Exception as exc:
                    status_widget.update(label="Error", state="error")
                    st.error(f"Processing failed: {exc}")
                    st.stop()

            st.session_state["results_upload"] = df_results

    if "results_upload" in st.session_state:
        df = st.session_state["results_upload"]
        st.success(f"✅ {len(df)} row(s) generated.")
        st.dataframe(df, width="stretch")
        st.download_button(
            label="⬇️ Download Excel",
            data=to_excel_bytes(df),
            file_name="fb_ad_urls.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    elif uploaded and not creds_ok:
        st.warning("Zoho CRM credentials are not configured. Check your local.env file.")

# ---------------------------------------------------------------------------
# Tab 2 — Direct ZIP upload (no Zoho credentials required)
# ---------------------------------------------------------------------------
with tab_zip:
    st.subheader("Upload a ZIP file containing Facebook HTML exports")
    st.caption("No Zoho CRM credentials required — the ZIP is processed locally.")

    zip_file = st.file_uploader(
        "Choose a ZIP file",
        type=["zip"],
        help="Upload a Facebook ad data export ZIP. Nested ZIPs are supported.",
    )

    if zip_file and st.button("▶ Extract & Process", key="btn_zip"):
        constructor = _build_constructor()
        zip_bytes = zip_file.read()
        label = zip_file.name

        progress_bar = st.progress(0.0)
        status_text = st.empty()

        with st.status("Extracting ZIP…", expanded=True) as status_widget:
            try:
                html_files = list(walk_zip(zip_bytes, label))
                status_widget.update(label=f"Found {len(html_files)} Facebook HTML file(s). Parsing…")

                rows: list[dict] = []
                total = len(html_files)

                if total == 0:
                    st.warning(
                        "No Facebook HTML export files were found inside the ZIP. "
                        "Make sure the ZIP contains files with the expected content."
                    )
                    status_widget.update(label="No matching files found.", state="error")
                else:
                    # --- Pass 1: Parse all HTML files ---
                    parsed_entries: list[tuple[str, str, list[str]]] = []
                    for idx, (display_path, html_text) in enumerate(html_files):
                        filename = display_path.split("/")[-1]
                        status_text.text(f"[{idx+1}/{total}] Parsing {filename}…")
                        st.write(f"[{idx+1}/{total}] Parsing {filename}…")

                        parsed = parse_html_content(display_path, html_text)
                        if parsed is None:
                            progress_bar.progress((idx + 1) / total * 0.5)
                            continue

                        generated_by = parsed["generated_by"]
                        keywords = parsed["keywords"]
                        targets = keywords if keywords else ([generated_by] if generated_by else [""])
                        parsed_entries.append((display_path, generated_by, targets))
                        progress_bar.progress((idx + 1) / total * 0.5)

                    # --- Batch URL construction (single LLM call) ---
                    all_names = [
                        kw or gb or ""
                        for (_, gb, tgts) in parsed_entries
                        for kw in tgts
                    ]
                    unique_names = list(dict.fromkeys(n for n in all_names if n))
                    status_text.text(f"Constructing URLs for {len(unique_names)} unique name(s)…")
                    st.write(f"Constructing URLs for {len(unique_names)} unique name(s)…")
                    url_map = constructor.batch_construct(unique_names)

                    # --- Pass 2: Build rows ---
                    for display_path, generated_by, targets in parsed_entries:
                        for keyword in targets:
                            company_name = keyword or generated_by or ""
                            url, confidence = url_map.get(company_name, ("", "UNKNOWN")) if company_name else ("", "UNKNOWN")
                            row = {
                                "Filename": display_path,
                                "Generated By": generated_by,
                                "Keywords Scraped": keyword,
                                "Constructed URL": url,
                                "Confidence": confidence,
                            }
                            if verify_urls:
                                cached = constructor._cache.get(
                                    constructor._cache_key(company_name), {}
                                )
                                row["URL Verified"] = cached.get("verified", False)
                            rows.append(row)

                    progress_bar.progress(1.0)
                    status_widget.update(label="Done!", state="complete")

                cols = ["Filename", "Generated By", "Keywords Scraped", "Constructed URL", "Confidence"]
                if verify_urls:
                    cols.append("URL Verified")
                df_zip = pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)
                st.session_state["results_zip"] = df_zip

            except Exception as exc:
                status_widget.update(label="Error", state="error")
                st.error(f"Processing failed: {exc}")

    if "results_zip" in st.session_state:
        df = st.session_state["results_zip"]
        st.success(f"✅ {len(df)} row(s) generated.")
        st.dataframe(df, width="stretch")
        st.download_button(
            label="⬇️ Download Excel",
            data=to_excel_bytes(df),
            file_name="fb_ad_urls_zip.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
