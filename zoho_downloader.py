"""
zoho_downloader.py — Zoho CRM OAuth2 client with recursive ZIP extraction.

Downloads ZIP attachments from Zoho CRM records and extracts Facebook HTML
export files from them, recursively handling nested archives.

Public API
----------
ZohoDownloader(...)
    .get_records_by_ids(ids) -> list[str]   (validates they exist)
    .collect_html_from_record(record_id) -> list[tuple[str, str]]
        Returns [(display_path, html_text), ...]
"""

from __future__ import annotations

import io
import logging
import time
import zipfile
from typing import Iterator, Optional

import requests

from fb_parser import HTML_REQUIRED_TOKENS, decode_bytes

logger = logging.getLogger(__name__)

MAX_ARCHIVE_DEPTH = 10


def walk_zip(
    data: bytes,
    label: str,
    depth: int = 0,
) -> Iterator[tuple[str, str]]:
    """
    Module-level helper: recursively walk a ZIP archive and yield
    (display_path, html_text) for every Facebook HTML export found.

    Usable without a ZohoDownloader instance (e.g. from direct ZIP uploads).
    """
    if depth > MAX_ARCHIVE_DEPTH:
        logger.warning("Max archive depth (%d) reached at %s", MAX_ARCHIVE_DEPTH, label)
        return

    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        logger.debug("Not a valid ZIP at depth %d: %s", depth, label)
        return

    with zf:
        for entry in zf.infolist():
            if entry.is_dir():
                continue
            entry_label = f"{label}/{entry.filename}"
            entry_lower = entry.filename.lower()

            if entry_lower.endswith(".zip"):
                try:
                    nested_bytes = zf.read(entry.filename)
                except Exception as exc:
                    logger.warning("Could not read nested ZIP %s: %s", entry_label, exc)
                    continue
                yield from walk_zip(nested_bytes, entry_label, depth + 1)
                continue

            if not entry_lower.endswith((".html", ".htm")):
                continue

            try:
                raw = zf.read(entry.filename)
            except Exception as exc:
                logger.warning("Could not read %s: %s", entry_label, exc)
                continue

            html_text = decode_bytes(raw)
            html_lower = html_text.lower()

            path_lower = entry_label.lower()
            if any(tok in path_lower or tok in html_lower for tok in HTML_REQUIRED_TOKENS):
                yield entry_label, html_text
_TOKEN_REFRESH_BUFFER = 60  # seconds before expiry to refresh proactively


class ZohoAuthError(RuntimeError):
    """Raised when Zoho token refresh fails."""


class ZohoDownloader:
    """
    Downloads attachments from a Zoho CRM module and extracts HTML files.

    Parameters
    ----------
    api_domain : str
        e.g. "https://www.zohoapis.com"
    accounts_domain : str
        e.g. "https://accounts.zoho.com"
    client_id : str
    client_secret : str
    refresh_token : str
    access_token : str
        Initial access token (may be empty; will be refreshed on first use).
    module : str
        CRM module name, default "Leads".
    api_version : str
        API version, default "v7".
    """

    def __init__(
        self,
        api_domain: str,
        accounts_domain: str,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        access_token: str = "",
        module: str = "Leads",
        api_version: str = "v7",
    ) -> None:
        self.api_domain = api_domain.rstrip("/")
        self.accounts_domain = accounts_domain.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self._access_token = access_token
        self._token_expiry: float = 0.0  # epoch seconds
        self._token_issued_by_us: bool = False
        self.module = module
        self.api_version = api_version
        self._session = requests.Session()

    # ------------------------------------------------------------------
    # OAuth2
    # ------------------------------------------------------------------

    def ensure_token(self) -> None:
        """Refresh the access token if it is missing or about to expire."""
        if not self._access_token:
            self._refresh_access_token()
            return
        # Only pre-emptively refresh if *we* issued this token and know its expiry.
        # For an externally-provided ACCESS_TOKEN we don't know the expiry, so we
        # trust it and let the 401-retry path in _get() handle actual expiry.
        if self._token_issued_by_us and time.time() >= self._token_expiry - _TOKEN_REFRESH_BUFFER:
            self._refresh_access_token()

    def _refresh_access_token(self) -> None:
        url = f"{self.accounts_domain}/oauth/v2/token"
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
        }
        resp = self._session.post(url, data=payload, timeout=30)
        if not resp.ok:
            raise ZohoAuthError(
                f"Token refresh failed [{resp.status_code}] posting to {url!r}. "
                f"Check that TOKEN_URL in local.env matches your Zoho data center "
                f"(e.g. accounts.zoho.com / accounts.zoho.eu / accounts.zoho.in). "
                f"Response: {resp.text[:500]}"
            )
        data = resp.json()
        if "access_token" not in data:
            raise ZohoAuthError(f"No access_token in refresh response: {data}")
        self._access_token = data["access_token"]
        expires_in = int(data.get("expires_in", 3600))
        self._token_expiry = time.time() + expires_in
        self._token_issued_by_us = True
        logger.debug("Zoho token refreshed; expires in %ds", expires_in)

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _get(self, url: str, **kwargs) -> requests.Response:
        """Perform an authorized GET, refreshing the token first."""
        self.ensure_token()
        kwargs.setdefault("timeout", 60)
        resp = self._session.get(
            url,
            headers={"Authorization": f"Zoho-oauthtoken {self._access_token}"},
            **kwargs,
        )
        if resp.status_code == 401:
            # Token may have been invalidated externally — try once more
            self._refresh_access_token()
            resp = self._session.get(
                url,
                headers={"Authorization": f"Zoho-oauthtoken {self._access_token}"},
                **kwargs,
            )
        return resp

    def _base_url(self) -> str:
        return f"{self.api_domain}/crm/{self.api_version}"

    # ------------------------------------------------------------------
    # Record helpers
    # ------------------------------------------------------------------

    def get_records_by_ids(self, ids: list[str]) -> list[str]:
        """
        Validate and return a de-duplicated list of record IDs that exist in
        the module.  Unknown IDs are silently dropped with a warning.
        """
        if not ids:
            return []
        # Zoho allows fetching up to 100 records by IDs in one call
        valid: list[str] = []
        for chunk_start in range(0, len(ids), 100):
            chunk = ids[chunk_start : chunk_start + 100]
            url = f"{self._base_url()}/{self.module}"
            resp = self._get(url, params={"ids": ",".join(chunk), "fields": "id"})
            if resp.status_code == 204:
                logger.warning("None of %s exist in %s", chunk, self.module)
                continue
            if not resp.ok:
                logger.warning(
                    "Batch ID lookup failed [%d]: %s", resp.status_code, resp.text[:200]
                )
                continue
            returned = resp.json().get("data", [])
            found_ids = {str(r["id"]) for r in returned}
            for rid in chunk:
                if rid in found_ids:
                    valid.append(rid)
                else:
                    logger.warning("Record ID %s not found in %s", rid, self.module)
        # Preserve order, de-duplicate
        seen: set[str] = set()
        result: list[str] = []
        for rid in valid:
            if rid not in seen:
                seen.add(rid)
                result.append(rid)
        return result

    # ------------------------------------------------------------------
    # Attachment helpers
    # ------------------------------------------------------------------

    def get_attachments(self, record_id: str) -> list[dict]:
        """
        Return a list of attachment metadata dicts for *record_id*.

        Each dict has at least: {"id": str, "File_Name": str, "Size": int}.
        """
        url = f"{self._base_url()}/{self.module}/{record_id}/Attachments?fields=id,File_Name"
        resp = self._get(url)
        if resp.status_code == 204:
            return []
        if not resp.ok:
            logger.warning(
                "Attachment list for %s failed [%d]: %s",
                record_id,
                resp.status_code,
                resp.text[:200],
            )
            return []
        return resp.json().get("data", [])

    def download_bytes(self, record_id: str, attachment_id: str) -> Optional[bytes]:
        """Download a single attachment and return its raw bytes."""
        url = (
            f"{self._base_url()}/{self.module}/{record_id}"
            f"/Attachments/{attachment_id}"
        )
        resp = self._get(url, stream=True)
        if not resp.ok:
            logger.warning(
                "Download failed for attachment %s on record %s [%d]",
                attachment_id,
                record_id,
                resp.status_code,
            )
            return None
        return resp.content

    # ------------------------------------------------------------------
    # ZIP walker
    # ------------------------------------------------------------------

    def _walk_zip(
        self,
        data: bytes,
        label: str,
        depth: int = 0,
    ) -> Iterator[tuple[str, str]]:
        """Delegate to the module-level walk_zip helper."""
        yield from walk_zip(data, label, depth)

    # ------------------------------------------------------------------
    # High-level pipeline
    # ------------------------------------------------------------------

    def collect_html_from_record(self, record_id: str) -> list[tuple[str, str]]:
        """
        Download all ZIP attachments for *record_id* and return a list of
        (display_path, html_text) tuples for every Facebook HTML export found.
        """
        results: list[tuple[str, str]] = []
        attachments = self.get_attachments(record_id)
        if not attachments:
            logger.debug("No attachments for record %s", record_id)
            return results

        for att in attachments:
            att_id = str(att.get("id", ""))
            filename = att.get("File_Name", "")
            if not att_id or not filename:
                continue

            filename_lower = filename.lower()

            raw = self.download_bytes(record_id, att_id)
            if raw is None:
                continue

            label = f"{record_id}/{filename}"

            if filename_lower.endswith(".zip"):
                found = list(self._walk_zip(raw, label))
                logger.info(
                    "Record %s / %s → %d Facebook HTML file(s) found",
                    record_id,
                    filename,
                    len(found),
                )
                results.extend(found)
            elif filename_lower.endswith((".html", ".htm")):
                html_text = decode_bytes(raw)
                html_lower = html_text.lower()
                if any(tok in html_lower for tok in HTML_REQUIRED_TOKENS):
                    results.append((label, html_text))
                    logger.info(
                        "Record %s / %s → Facebook HTML file found directly",
                        record_id,
                        filename,
                    )
                else:
                    logger.debug("Skipping non-Facebook HTML attachment: %s", filename)
            else:
                logger.debug("Skipping non-ZIP/HTML attachment: %s", filename)

        return results
