"""Google Places API (New) — secondary enrichment source.

Uses the $200/month free Google Maps credit. Only called for leads
missing website or phone after Overpass scrape.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.utils.logging import get_logger
from app.utils.retry import with_retry

logger = get_logger(__name__)

PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"


@with_retry(max_attempts=3, min_wait=1.0, max_wait=8.0)
def enrich_via_places(
    business_name: str,
    city: str,
    api_key: str,
) -> dict[str, Any] | None:
    """Search Google Places for a business and return enrichment data.

    Args:
        business_name: Name of the business to search.
        city: City to narrow search.
        api_key: Google Maps API key.

    Returns:
        Dict with website, phone, address, or None if not found.
    """
    if not api_key:
        return None

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.displayName,"
            "places.formattedAddress,"
            "places.nationalPhoneNumber,"
            "places.websiteUri,"
            "places.googleMapsUri"
        ),
    }

    payload = {
        "textQuery": f"{business_name} {city}",
        "maxResultCount": 1,
    }

    with httpx.Client(timeout=15.0) as client:
        resp = client.post(PLACES_TEXT_SEARCH_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    places = data.get("places", [])
    if not places:
        logger.info("places_no_result", business=business_name, city=city)
        return None

    place = places[0]
    result: dict[str, Any] = {}

    if website := place.get("websiteUri"):
        result["website"] = website
    if phone := place.get("nationalPhoneNumber"):
        result["phone"] = phone
    if address := place.get("formattedAddress"):
        result["address"] = address

    logger.info("places_enriched", business=business_name, fields=list(result.keys()))
    return result if result else None
