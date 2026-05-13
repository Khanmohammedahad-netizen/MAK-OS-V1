"""Yelp Fusion API — tertiary fallback source.

Free tier: 500 API calls/day. Used only when Overpass + Google Places
fail to provide sufficient data for a lead.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.utils.logging import get_logger
from app.utils.retry import with_retry

logger = get_logger(__name__)

YELP_SEARCH_URL = "https://api.yelp.com/v3/businesses/search"

NICHE_YELP_CATEGORIES: dict[str, str] = {
    "restaurant": "restaurants,cafes",
    "salon": "hair,beautysvc",
    "clinic": "dentists,physicians",
    "trades": "plumbing,electricians",
    "generic": "restaurants,hair,dentists",
}


@with_retry(max_attempts=3, min_wait=1.0, max_wait=8.0)
def search_yelp(
    niche: str,
    city: str,
    api_key: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search Yelp for businesses matching niche + city.

    Args:
        niche: Target niche keyword.
        city: Target city.
        api_key: Yelp Fusion API key (Bearer token).
        limit: Max results per call (Yelp max 50).

    Returns:
        List of lead dicts ready for upsert.
    """
    if not api_key:
        return []

    categories = NICHE_YELP_CATEGORIES.get(niche, "restaurants")
    headers = {"Authorization": api_key}
    params: dict[str, Any] = {
        "location": city,
        "categories": categories,
        "limit": min(limit, 50),
        "sort_by": "rating",
    }

    with httpx.Client(timeout=15.0) as client:
        resp = client.get(YELP_SEARCH_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

    businesses = data.get("businesses", [])
    leads: list[dict[str, Any]] = []

    for biz in businesses:
        location = biz.get("location", {})
        leads.append(
            {
                "source": "yelp",
                "source_id": biz.get("id", ""),
                "business_name": biz.get("name", ""),
                "website": biz.get("url", ""),
                "email": None,
                "phone": biz.get("phone", ""),
                "city": location.get("city", ""),
                "region": location.get("state", ""),
                "country": location.get("country", ""),
                "category": ",".join(
                    c.get("alias", "") for c in biz.get("categories", [])
                ),
                "address": ", ".join(location.get("display_address", [])),
                "socials": {},
                "raw_payload": biz,
            }
        )

    logger.info("yelp_results", count=len(leads), city=city, niche=niche)
    return leads
