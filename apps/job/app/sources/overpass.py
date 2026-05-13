"""Overpass API source — primary lead scraper using OpenStreetMap data."""

from __future__ import annotations

from typing import Any

import overpy

from app.utils.logging import get_logger
from app.utils.retry import with_retry

logger = get_logger(__name__)

# Mapping of niche keywords to OSM amenity/shop/craft tags
NICHE_TAG_MAP: dict[str, list[tuple[str, str]]] = {
    "restaurant": [
        ("amenity", "restaurant"),
        ("amenity", "cafe"),
        ("amenity", "fast_food"),
    ],
    "salon": [
        ("shop", "hairdresser"),
        ("shop", "beauty"),
    ],
    "clinic": [
        ("amenity", "clinic"),
        ("amenity", "dentist"),
        ("amenity", "doctors"),
    ],
    "trades": [
        ("craft", "plumber"),
        ("craft", "electrician"),
        ("craft", "carpenter"),
        ("shop", "trade"),
    ],
    "generic": [
        ("amenity", "restaurant"),
        ("shop", "hairdresser"),
        ("amenity", "clinic"),
    ],
}


def _build_query(bbox: tuple[float, float, float, float], niche: str) -> str:
    """Build Overpass QL query for the given bounding box and niche."""
    south, west, north, east = bbox
    bbox_str = f"{south},{west},{north},{east}"

    tags = NICHE_TAG_MAP.get(niche, NICHE_TAG_MAP["generic"])
    node_queries = []
    for key, value in tags:
        node_queries.append(f'  node["{key}"="{value}"]({bbox_str});')
        node_queries.append(f'  way["{key}"="{value}"]({bbox_str});')

    query_body = "\n".join(node_queries)
    return f"""
[out:json][timeout:60];
(
{query_body}
);
out center body;
"""


def _extract_lead(element: Any) -> dict[str, Any] | None:
    """Extract lead data from an Overpass element."""
    tags: dict[str, str] = element.tags if hasattr(element, "tags") else {}
    name = tags.get("name")
    if not name:
        return None

    lat: float | None = None
    lon: float | None = None
    if hasattr(element, "lat") and element.lat is not None:
        lat = float(element.lat)
        lon = float(element.lon)
    elif hasattr(element, "center_lat") and element.center_lat is not None:
        lat = float(element.center_lat)
        lon = float(element.center_lon)

    address_parts = [
        tags.get("addr:housenumber", ""),
        tags.get("addr:street", ""),
        tags.get("addr:city", ""),
        tags.get("addr:postcode", ""),
    ]
    address = ", ".join(p for p in address_parts if p)

    return {
        "source": "overpass",
        "source_id": str(element.id),
        "business_name": name,
        "website": tags.get("website") or tags.get("contact:website"),
        "email": tags.get("email") or tags.get("contact:email"),
        "phone": tags.get("phone") or tags.get("contact:phone"),
        "city": tags.get("addr:city", ""),
        "region": tags.get("addr:state", ""),
        "country": tags.get("addr:country", ""),
        "category": tags.get("amenity") or tags.get("shop") or tags.get("craft") or "",
        "address": address,
        "socials": {
            "facebook": tags.get("contact:facebook", ""),
            "instagram": tags.get("contact:instagram", ""),
            "twitter": tags.get("contact:twitter", ""),
        },
        "raw_payload": {
            "lat": lat,
            "lon": lon,
            "osm_tags": tags,
        },
    }


@with_retry(max_attempts=3, min_wait=2.0, max_wait=15.0)
def scrape_overpass(
    bbox: tuple[float, float, float, float],
    niche: str,
    cap: int = 50,
) -> list[dict[str, Any]]:
    """Scrape leads from OpenStreetMap via Overpass API.

    Args:
        bbox: Bounding box (south, west, north, east).
        niche: Target niche keyword.
        cap: Maximum number of leads to return.

    Returns:
        List of lead dicts ready for upsert.
    """
    api = overpy.Overpass()
    query = _build_query(bbox, niche)
    logger.info("overpass_query", niche=niche, bbox=bbox)

    result = api.query(query)

    leads: list[dict[str, Any]] = []
    for element in [*result.nodes, *result.ways]:
        if len(leads) >= cap:
            break
        lead = _extract_lead(element)
        if lead:
            leads.append(lead)

    logger.info("overpass_results", count=len(leads), cap=cap)
    return leads
