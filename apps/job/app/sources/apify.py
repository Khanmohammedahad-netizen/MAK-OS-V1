"""Apify source — optional plugin gated by APIFY_ENABLED env var.

Disabled by default. When enabled, can be used as an additional
lead source via Apify actors (e.g., Google Maps scraper).
"""

from __future__ import annotations

from typing import Any

import httpx

from app.utils.logging import get_logger
from app.utils.retry import with_retry

logger = get_logger(__name__)

APIFY_RUN_URL = "https://api.apify.com/v2/acts/{actor_id}/runs"
APIFY_DATASET_URL = "https://api.apify.com/v2/datasets/{dataset_id}/items"


@with_retry(max_attempts=2, min_wait=3.0, max_wait=15.0)
def run_apify_actor(
    actor_id: str,
    run_input: dict[str, Any],
    token: str,
    timeout_secs: int = 120,
) -> list[dict[str, Any]]:
    """Run an Apify actor and return its dataset items.

    Args:
        actor_id: Apify actor ID (e.g., "drobnikj/crawler-google-places").
        run_input: Actor input configuration.
        token: Apify API token.
        timeout_secs: Max wait for actor completion.

    Returns:
        List of raw result items from the actor's dataset.
    """
    if not token:
        logger.warning("apify_no_token")
        return []

    headers = {"Authorization": f"Bearer {token}"}
    url = APIFY_RUN_URL.format(actor_id=actor_id)

    with httpx.Client(timeout=float(timeout_secs)) as client:
        # Start the actor run synchronously (waits for completion)
        resp = client.post(
            url,
            json=run_input,
            headers=headers,
            params={"waitForFinish": timeout_secs},
        )
        resp.raise_for_status()
        run_data = resp.json()

    dataset_id = run_data.get("data", {}).get("defaultDatasetId")
    if not dataset_id:
        logger.warning("apify_no_dataset", actor=actor_id)
        return []

    # Fetch dataset items
    dataset_url = APIFY_DATASET_URL.format(dataset_id=dataset_id)
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(dataset_url, headers=headers, params={"limit": 100})
        resp.raise_for_status()
        items: list[dict[str, Any]] = resp.json()

    logger.info("apify_results", actor=actor_id, count=len(items))
    return items


def apify_to_leads(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert Apify Google Places results to standard lead format."""
    leads: list[dict[str, Any]] = []
    for item in items:
        name = item.get("title") or item.get("name")
        if not name:
            continue
        leads.append(
            {
                "source": "apify",
                "source_id": item.get("placeId", ""),
                "business_name": name,
                "website": item.get("website"),
                "email": item.get("email"),
                "phone": item.get("phone"),
                "city": item.get("city", ""),
                "region": item.get("state", ""),
                "country": item.get("countryCode", ""),
                "category": item.get("categoryName", ""),
                "address": item.get("address", ""),
                "socials": {},
                "raw_payload": item,
            }
        )
    return leads
