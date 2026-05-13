"""Website audit — lightweight analysis using httpx + selectolax.

No headless browser. Checks reachability, HTTPS, meta tags, forms,
CTAs, booking systems, and WhatsApp links.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import httpx
from selectolax.parser import HTMLParser

from app.utils.logging import get_logger
from app.utils.retry import with_retry

logger = get_logger(__name__)

GENERIC_EMAIL_DOMAINS = {"gmail.com", "outlook.com", "yahoo.com", "hotmail.com", "aol.com"}

BOOKING_KEYWORDS = [
    "book", "booking", "reserve", "reservation", "appointment",
    "schedule", "calendly", "acuity", "booksy", "treatwell",
    "opentable", "resy", "square", "fresha", "vagaro",
]

CTA_KEYWORDS = [
    "order", "buy", "shop", "get started", "sign up",
    "free trial", "get quote", "contact us", "enquire",
]


def _is_generic_email(email: str | None) -> bool:
    """Check if an email uses a generic provider domain."""
    if not email:
        return False
    domain = email.split("@")[-1].lower() if "@" in email else ""
    return domain in GENERIC_EMAIL_DOMAINS


def _check_text_for_keywords(text: str, keywords: list[str]) -> bool:
    """Check if any keyword appears in text (case-insensitive)."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


@with_retry(max_attempts=2, min_wait=1.0, max_wait=5.0)
def _fetch_page(url: str) -> tuple[str, bool, str]:
    """Fetch a page and return (html, is_https, final_url)."""
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    with httpx.Client(
        timeout=15.0,
        follow_redirects=True,
        headers={"User-Agent": "MAKLeadEngine/1.0 (audit)"},
    ) as client:
        resp = client.get(url)
        resp.raise_for_status()
        is_https = resp.url.scheme == "https"
        return resp.text, is_https, str(resp.url)


def audit_website(lead_id: str, website: str, email: str | None = None) -> dict[str, Any]:
    """Run a lightweight audit on a business website.

    Args:
        lead_id: UUID of the lead.
        website: URL to audit.
        email: Lead's email address (to check if generic).

    Returns:
        Dict ready for insert into audits table.
    """
    result: dict[str, Any] = {
        "lead_id": lead_id,
        "reachable": False,
        "https": False,
        "has_title": False,
        "has_meta_desc": False,
        "has_viewport": False,
        "has_contact_form": False,
        "has_cta": False,
        "has_booking": False,
        "has_whatsapp": False,
        "generic_email": _is_generic_email(email),
        "weakness_summary": "",
        "audit_score": 0,
    }

    try:
        html, is_https, final_url = _fetch_page(website)
    except Exception as exc:
        logger.warning("audit_unreachable", website=website, error=str(exc))
        result["weakness_summary"] = "Website is unreachable or returns an error."
        return result

    result["reachable"] = True
    result["https"] = is_https

    # Parse HTML
    tree = HTMLParser(html)

    # Title
    title_node = tree.css_first("title")
    result["has_title"] = bool(title_node and title_node.text(strip=True))

    # Meta description
    meta_desc = tree.css_first('meta[name="description"]')
    result["has_meta_desc"] = bool(
        meta_desc and meta_desc.attributes.get("content", "").strip()
    )

    # Viewport
    viewport = tree.css_first('meta[name="viewport"]')
    result["has_viewport"] = bool(viewport)

    # Contact form
    forms = tree.css("form")
    has_form = False
    for form in forms:
        form_html = form.html or ""
        if any(
            kw in form_html.lower()
            for kw in ["email", "contact", "message", "enquir", "name"]
        ):
            has_form = True
            break
    result["has_contact_form"] = has_form

    # Full page text for keyword checks
    body = tree.css_first("body")
    page_text = body.text() if body else ""
    page_html = html.lower()

    # CTA check
    result["has_cta"] = _check_text_for_keywords(page_text, CTA_KEYWORDS)

    # Booking check
    result["has_booking"] = _check_text_for_keywords(page_html, BOOKING_KEYWORDS)

    # WhatsApp
    result["has_whatsapp"] = "whatsapp" in page_html or "wa.me" in page_html

    # Build weakness summary
    weaknesses: list[str] = []
    if not result["https"]:
        weaknesses.append("No HTTPS")
    if not result["has_title"]:
        weaknesses.append("Missing page title")
    if not result["has_meta_desc"]:
        weaknesses.append("No meta description")
    if not result["has_viewport"]:
        weaknesses.append("Not mobile-optimised")
    if not result["has_contact_form"]:
        weaknesses.append("No contact form")
    if not result["has_cta"]:
        weaknesses.append("No clear call-to-action")
    if not result["has_booking"]:
        weaknesses.append("No online booking system")
    if result["generic_email"]:
        weaknesses.append("Uses generic email (Gmail/Outlook)")

    result["weakness_summary"] = "; ".join(weaknesses) if weaknesses else "No major issues found"

    # Audit score: count of weaknesses found (higher = worse site = better lead)
    result["audit_score"] = len(weaknesses)

    logger.info(
        "audit_complete",
        website=website,
        reachable=True,
        weaknesses=len(weaknesses),
    )
    return result
