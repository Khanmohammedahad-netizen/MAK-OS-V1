"""Deduplication utilities for lead normalization."""

from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse


def normalize_domain(website: str | None) -> str:
    """Extract and normalize domain from a URL.

    Strips protocol, www prefix, trailing slashes, and lowercases.
    Returns empty string if input is None or unparseable.
    """
    if not website:
        return ""
    try:
        parsed = urlparse(website if "://" in website else f"https://{website}")
        domain = (parsed.netloc or parsed.path).lower().strip()
        domain = re.sub(r"^www\.", "", domain)
        domain = domain.rstrip("/")
        return domain
    except Exception:
        return ""


def normalize_phone(phone: str | None) -> str:
    """Strip all non-digit characters from phone number."""
    if not phone:
        return ""
    return re.sub(r"[^\d]", "", phone)


def slugify(text: str | None) -> str:
    """Create a URL-safe slug from text.

    Lowercases, strips non-alphanumeric, collapses whitespace to hyphens.
    """
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text)
    return text.strip("-")


def compute_dedupe_key(
    website: str | None,
    phone: str | None,
    business_name: str | None,
) -> str:
    """Compute SHA-256 dedupe key from normalized domain + phone + slug(name).

    Concatenates with `||` separator, then hashes.
    """
    parts = [
        normalize_domain(website),
        normalize_phone(phone),
        slugify(business_name),
    ]
    combined = "||".join(parts)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()
