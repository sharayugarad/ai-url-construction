"""
url_constructor.py — Tiered URL construction with LLM fallback and cache.

Confidence tiers
----------------
HIGH   — company name found in BRAND_MAP, or name already contains a domain.
MEDIUM — OpenAI GPT-4o-mini returns a plausible URL.
LOW    — Slug guess: <slugified-name>.com
UNKNOWN— All tiers failed or returned "unknown".

Public API
----------
URLConstructor(openai_api_key, cache_path, verify_urls)
    .construct(company_name) -> (url, confidence)
    .verify(url) -> bool
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Known brand map  (lower-cased key → canonical URL)
# ---------------------------------------------------------------------------
BRAND_MAP: dict[str, str] = {
    "tiktok": "https://www.tiktok.com",
    "instagram": "https://www.instagram.com",
    "twitter": "https://www.twitter.com",
    "x": "https://www.x.com",
    "linkedin": "https://www.linkedin.com",
    "spotify": "https://www.spotify.com",
    "netflix": "https://www.netflix.com",
    "hulu": "https://www.hulu.com",
    "disney+": "https://www.disneyplus.com",
    "disney plus": "https://www.disneyplus.com",
    "crunchyroll": "https://www.crunchyroll.com",
    "youtube": "https://www.youtube.com",
    "doordash": "https://www.doordash.com",
    "chewy": "https://www.chewy.com",
    "uber": "https://www.uber.com",
    "uber eats": "https://www.ubereats.com",
    "amazon": "https://www.amazon.com",
    "ebay": "https://www.ebay.com",
    "walmart": "https://www.walmart.com",
    "target": "https://www.target.com",
    "oracle": "https://www.oracle.com",
    "facebook": "https://www.facebook.com",
    "meta": "https://www.meta.com",
    "google": "https://www.google.com",
    "apple": "https://www.apple.com",
    "microsoft": "https://www.microsoft.com",
    "samsung": "https://www.samsung.com",
    "shopify": "https://www.shopify.com",
    "airbnb": "https://www.airbnb.com",
    "lyft": "https://www.lyft.com",
    "grubhub": "https://www.grubhub.com",
    "etsy": "https://www.etsy.com",
    "pinterest": "https://www.pinterest.com",
    "snapchat": "https://www.snapchat.com",
    "reddit": "https://www.reddit.com",
    "twitch": "https://www.twitch.tv",
    "discord": "https://www.discord.com",
    "zoom": "https://www.zoom.us",
    "slack": "https://www.slack.com",
    "dropbox": "https://www.dropbox.com",
    "paypal": "https://www.paypal.com",
    "stripe": "https://www.stripe.com",
    "square": "https://squareup.com",
    "salesforce": "https://www.salesforce.com",
    "hubspot": "https://www.hubspot.com",
    "mailchimp": "https://www.mailchimp.com",
    "adobe": "https://www.adobe.com",
    "canva": "https://www.canva.com",
    "notion": "https://www.notion.so",
    "asana": "https://www.asana.com",
    "trello": "https://www.trello.com",
    "github": "https://www.github.com",
    "gitlab": "https://www.gitlab.com",
    "atlassian": "https://www.atlassian.com",
    "jira": "https://www.atlassian.com/software/jira",
    "netflix": "https://www.netflix.com",
    "hbo": "https://www.hbo.com",
    "peacock": "https://www.peacocktv.com",
    "paramount+": "https://www.paramountplus.com",
    "paramount plus": "https://www.paramountplus.com",
    "apple tv+": "https://tv.apple.com",
    "apple tv plus": "https://tv.apple.com",
    "best buy": "https://www.bestbuy.com",
    "costco": "https://www.costco.com",
    "home depot": "https://www.homedepot.com",
    "lowe's": "https://www.lowes.com",
    "lowes": "https://www.lowes.com",
    "ikea": "https://www.ikea.com",
    "wayfair": "https://www.wayfair.com",
    "nordstrom": "https://www.nordstrom.com",
    "macy's": "https://www.macys.com",
    "macys": "https://www.macys.com",
    "gap": "https://www.gap.com",
    "h&m": "https://www.hm.com",
    "zara": "https://www.zara.com",
    "nike": "https://www.nike.com",
    "adidas": "https://www.adidas.com",
    "puma": "https://www.puma.com",
    "under armour": "https://www.underarmour.com",
    "lululemon": "https://www.lululemon.com",
    "starbucks": "https://www.starbucks.com",
    "mcdonald's": "https://www.mcdonalds.com",
    "mcdonalds": "https://www.mcdonalds.com",
    "burger king": "https://www.bk.com",
    "subway": "https://www.subway.com",
    "domino's": "https://www.dominos.com",
    "dominos": "https://www.dominos.com",
    "pizza hut": "https://www.pizzahut.com",
    "chipotle": "https://www.chipotle.com",
    "panera": "https://www.panerabread.com",
    "panera bread": "https://www.panerabread.com",
}

# Regex to detect if the company name already contains a domain
_DOMAIN_RE = re.compile(
    r"(?:https?://)?(?:www\.)?[\w\-]+\."
    r"(?:com|org|net|io|co|app|ai|us|uk|ca|de|fr|au|jp|in|br)\b",
    re.I,
)

# Characters to strip when building a slug
_SLUG_STRIP_RE = re.compile(r"[^a-z0-9]+")


class URLConstructor:
    """
    Construct a website URL for a company name using a tiered strategy.

    Parameters
    ----------
    openai_api_key : str
        OpenAI API key for GPT-4o-mini (MEDIUM tier). Leave empty to skip.
    cache_path : str | Path
        Path to the JSON cache file.  Created if absent.
    verify_urls : bool
        If True, issue an HTTP HEAD request to verify constructed URLs.
    llm_timeout : float
        Seconds to wait for the OpenAI API (default 15).
    verify_timeout : float
        Seconds to wait for HTTP HEAD verification (default 5).
    """

    def __init__(
        self,
        openai_api_key: str = "",
        cache_path: str | Path = "url_cache.json",
        verify_urls: bool = False,
        llm_timeout: float = 15.0,
        verify_timeout: float = 5.0,
    ) -> None:
        self.openai_api_key = openai_api_key
        self.cache_path = Path(cache_path)
        self.verify_urls = verify_urls
        self.llm_timeout = llm_timeout
        self.verify_timeout = verify_timeout
        self._cache: dict[str, dict] = {}
        self._session = requests.Session()
        self._openai_client = None
        self.load_cache()

        if openai_api_key:
            try:
                import openai  # type: ignore

                self._openai_client = openai.OpenAI(api_key=openai_api_key)
            except ImportError:
                logger.warning(
                    "openai package not installed — MEDIUM tier disabled. "
                    "Install with: pip install openai"
                )

    # ------------------------------------------------------------------
    # Cache
    # ------------------------------------------------------------------

    def load_cache(self) -> None:
        """Load the JSON cache from disk (silently ignores missing files)."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, encoding="utf-8") as fh:
                    self._cache = json.load(fh)
                logger.debug("Loaded %d cache entries from %s", len(self._cache), self.cache_path)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Could not load cache %s: %s", self.cache_path, exc)
                self._cache = {}

    def save_cache(self) -> None:
        """Persist the in-memory cache to disk."""
        try:
            with open(self.cache_path, "w", encoding="utf-8") as fh:
                json.dump(self._cache, fh, indent=2, ensure_ascii=False)
        except OSError as exc:
            logger.warning("Could not save cache to %s: %s", self.cache_path, exc)

    def _cache_key(self, name: str) -> str:
        return name.strip().lower()

    # ------------------------------------------------------------------
    # Tiered construction
    # ------------------------------------------------------------------

    def _high(self, name: str) -> Optional[str]:
        """HIGH tier: brand map lookup or embedded domain extraction."""
        lower = name.strip().lower()

        # Direct brand map lookup
        if lower in BRAND_MAP:
            return BRAND_MAP[lower]

        # Partial brand map lookup (name contains a known brand)
        for brand, url in BRAND_MAP.items():
            if brand in lower:
                return url

        # Name already contains a URL/domain
        m = _DOMAIN_RE.search(name)
        if m:
            domain = m.group(0)
            if not domain.startswith("http"):
                domain = "https://" + domain
            return domain

        return None

    def _medium_llm(self, name: str) -> Optional[str]:
        """MEDIUM tier: ask GPT-4o-mini for the official website URL."""
        if self._openai_client is None:
            return None
        try:
            prompt = (
                f'What is the official website URL for the company or brand named "{name}"? '
                'Reply with ONLY the URL (e.g. https://www.example.com) or the single word "unknown".'
            )
            response = self._openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0,
                timeout=self.llm_timeout,
            )
            text = response.choices[0].message.content.strip().lower()
            if text in ("unknown", "", "n/a", "none"):
                return None
            # Ensure it looks like a URL
            if "." in text and not text.startswith("http"):
                text = "https://" + text
            if re.match(r"https?://", text):
                return text
            return None
        except Exception as exc:
            logger.warning("LLM URL lookup failed for %r: %s", name, exc)
            return None

    def _medium_llm_batch(self, names: list[str]) -> dict[str, Optional[str]]:
        """Single LLM call for multiple company names. Returns name → url (or None)."""
        if self._openai_client is None or not names:
            return {}
        try:
            names_list = "\n".join(f"- {n}" for n in names)
            prompt = (
                "For each company/brand listed below, provide their official website URL.\n"
                'Reply with ONLY a JSON object mapping each name to its URL or "unknown".\n'
                'Example: {"Acme Corp": "https://www.acme.com", "Unknown Co": "unknown"}\n\n'
                f"Companies:\n{names_list}"
            )
            response = self._openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=min(max(200, len(names) * 60), 16384),
                temperature=0,
                timeout=self.llm_timeout,
            )
            text = response.choices[0].message.content.strip()
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                m = re.search(r"\{.*\}", text, re.DOTALL)
                if not m:
                    return {}
                data = json.loads(m.group(0))
            result: dict[str, Optional[str]] = {}
            for name, url in data.items():
                if not isinstance(url, str):
                    continue
                url = url.strip()
                if url.lower() in ("unknown", "", "n/a", "none"):
                    result[name] = None
                    continue
                if "." in url and not url.startswith("http"):
                    url = "https://" + url
                if re.match(r"https?://", url):
                    result[name] = url
                else:
                    result[name] = None
            return result
        except Exception as exc:
            logger.warning("Batch LLM URL lookup failed: %s", exc)
            return {}

    def batch_construct(self, company_names: list[str]) -> dict[str, tuple[str, str]]:
        """
        Efficiently construct URLs for many company names.

        - Resolves HIGH tier locally for all names (no API call).
        - Sends remaining unknowns to the LLM in a single batched API call.
        - Saves the cache once at the end.

        Returns dict mapping each company_name -> (url, confidence).
        """
        results: dict[str, tuple[str, str]] = {}
        needs_llm: list[str] = []
        cache_dirty = False

        for name in company_names:
            if not name or not name.strip():
                results[name] = ("", "UNKNOWN")
                continue
            cache_key = self._cache_key(name)
            if cache_key in self._cache:
                entry = self._cache[cache_key]
                results[name] = (entry["url"], entry["confidence"])
                continue
            url = self._high(name)
            if url:
                results[name] = (url, "HIGH")
                self._cache[cache_key] = {"url": url, "confidence": "HIGH", "verified": False}
                cache_dirty = True
            else:
                needs_llm.append(name)

        if needs_llm:
            logger.info("Batch LLM lookup for %d company name(s).", len(needs_llm))
            llm_results = self._medium_llm_batch(needs_llm)
            for name in needs_llm:
                cache_key = self._cache_key(name)
                url = llm_results.get(name)
                if url:
                    confidence = "MEDIUM"
                else:
                    url = self._low_slug(name) or ""
                    confidence = "LOW" if url else "UNKNOWN"
                results[name] = (url, confidence)
                self._cache[cache_key] = {"url": url, "confidence": confidence, "verified": False}
            cache_dirty = True

        if cache_dirty:
            self.save_cache()

        return results

    def _low_slug(self, name: str) -> Optional[str]:
        """LOW tier: generate a slug URL from the company name."""
        slug = _SLUG_STRIP_RE.sub("", name.strip().lower())
        if not slug:
            return None
        return f"https://www.{slug}.com"

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def verify(self, url: str) -> bool:
        """
        Issue an HTTP HEAD request to check if *url* is reachable.

        Returns True for 2xx / 3xx responses, False otherwise.
        """
        try:
            resp = self._session.head(
                url,
                timeout=self.verify_timeout,
                allow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; URLVerifier/1.0)"},
            )
            return resp.status_code < 400
        except requests.RequestException as exc:
            logger.debug("URL verification failed for %s: %s", url, exc)
            return False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def construct(self, company_name: str) -> tuple[str, str]:
        """
        Construct a URL for *company_name*.

        Returns
        -------
        (url, confidence) where confidence is one of:
            "HIGH", "MEDIUM", "LOW", "UNKNOWN"
        """
        if not company_name or not company_name.strip():
            return ("", "UNKNOWN")

        cache_key = self._cache_key(company_name)

        # Cache hit
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            logger.debug("Cache hit for %r → %s (%s)", company_name, entry["url"], entry["confidence"])
            return entry["url"], entry["confidence"]

        url: Optional[str] = None
        confidence: str = "UNKNOWN"

        # Tier 1 — HIGH
        url = self._high(company_name)
        if url:
            confidence = "HIGH"

        # Tier 2 — MEDIUM (LLM)
        if url is None:
            url = self._medium_llm(company_name)
            if url:
                confidence = "MEDIUM"

        # Tier 3 — LOW (slug)
        if url is None:
            url = self._low_slug(company_name)
            if url:
                confidence = "LOW"

        if url is None:
            url = ""
            confidence = "UNKNOWN"

        # Optional HTTP HEAD verification
        verified = False
        if url and self.verify_urls:
            verified = self.verify(url)

        # Store in cache
        self._cache[cache_key] = {
            "url": url,
            "confidence": confidence,
            "verified": verified,
        }
        self.save_cache()

        logger.debug(
            "Constructed URL for %r → %s (%s, verified=%s)",
            company_name,
            url,
            confidence,
            verified,
        )
        return url, confidence
