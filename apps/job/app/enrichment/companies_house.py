"""Companies House API enrichment — UK leads only.

Free Public Data API: 600 requests per 5 minutes.
Searches by company name and returns best match.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.utils.logging import get_logger
from app.utils.retry import with_retry

logger = get_logger(__name__)

SEARCH_URL = "https://api.company-information.service.gov.uk/search/companies"


@with_retry(max_attempts=3, min_wait=1.0, max_wait=8.0)
def enrich_companies_house(
    business_name: str,
    lead_id: str,
    api_key: str,
) -> dict[str, Any] | None:
    """Search Companies House for a UK business and return enrichment data.

    Args:
        business_name: Name of the business to search.
        lead_id: UUID of the lead row.
        api_key: Companies House API key.

    Returns:
        Dict ready for insert into enrichment_companies_house, or None.
    """
    if not api_key:
        return None

    with httpx.Client(timeout=15.0, auth=(api_key, "")) as client:
        resp = client.get(SEARCH_URL, params={"q": business_name, "items_per_page": 3})
        resp.raise_for_status()
        data = resp.json()

    items = data.get("items", [])
    if not items:
        logger.info("ch_no_results", business=business_name)
        return None

    # Pick best match — first result from Companies House is ranked by relevance
    best = items[0]

    # Compute rough match confidence based on name similarity
    ch_name = (best.get("title") or "").lower().strip()
    query_name = business_name.lower().strip()
    confidence = 1.0 if ch_name == query_name else 0.7 if query_name in ch_name else 0.4

    enrichment: dict[str, Any] = {
        "lead_id": lead_id,
        "company_number": best.get("company_number"),
        "company_status": best.get("company_status"),
        "incorporation_date": best.get("date_of_creation"),
        "sic_codes": best.get("sic_codes") or [],
        "officers_summary": {
            "title": best.get("title"),
            "address_snippet": best.get("address_snippet"),
            "company_type": best.get("company_type"),
        },
        "match_confidence": confidence,
    }

    logger.info(
        "ch_enriched",
        business=business_name,
        company_number=enrichment["company_number"],
        confidence=confidence,
    )
    return enrichment
