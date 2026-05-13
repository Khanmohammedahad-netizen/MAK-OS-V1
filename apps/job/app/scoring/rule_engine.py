"""Rule-based lead scoring engine — fully transparent and deterministic.

Each rule contributes a known amount to the final score. The breakdown
and reasons are stored alongside the score for dashboard visibility.
"""

from __future__ import annotations

from typing import Any

from app.utils.logging import get_logger

logger = get_logger(__name__)

TARGET_NICHES = {"restaurant", "salon", "clinic", "trades", "cafe", "dentist", "hairdresser"}


def score_lead(
    lead: dict[str, Any],
    audit: dict[str, Any] | None,
    enrichment: dict[str, Any] | None,
    is_blacklisted: bool,
    recently_contacted: bool,
    target_niche: str,
) -> dict[str, Any]:
    """Score a lead using transparent weighted rules.

    Args:
        lead: Lead row from database.
        audit: Audit row (or None if no audit).
        enrichment: Companies House enrichment (or None).
        is_blacklisted: Whether the lead is blacklisted.
        recently_contacted: Whether lead was contacted in last 30 days.
        target_niche: Current target niche.

    Returns:
        Dict with lead_id, final_score, breakdown, reasons — ready for insert.
    """
    score = 0
    breakdown: dict[str, int] = {}
    reasons: list[str] = []

    # ── Positive signals from audit ──
    if audit:
        if not audit.get("has_booking"):
            score += 20
            breakdown["no_booking_cta"] = 20
            reasons.append("No online booking or ordering system")

        if not audit.get("has_contact_form"):
            score += 15
            breakdown["no_contact_form"] = 15
            reasons.append("No contact form on website")

        if audit.get("generic_email"):
            score += 15
            breakdown["generic_email"] = 15
            reasons.append("Uses generic email provider (Gmail/Outlook)")

        if not audit.get("has_viewport"):
            score += 10
            breakdown["no_mobile_viewport"] = 10
            reasons.append("Website not optimised for mobile")

        if not audit.get("https"):
            score += 10
            breakdown["no_https"] = 10
            reasons.append("No HTTPS — site is insecure")
    else:
        # No website at all is a strong signal
        if not lead.get("website"):
            score += 25
            breakdown["no_website"] = 25
            reasons.append("No website found")

    # ── UK Companies House bonus ──
    if enrichment and enrichment.get("company_status") == "active":
        score += 10
        breakdown["ch_active"] = 10
        reasons.append("UK registered company (active)")

    # ── Niche match ──
    lead_category = (lead.get("category") or "").lower()
    if lead_category in TARGET_NICHES or target_niche.lower() in lead_category:
        score += 5
        breakdown["niche_match"] = 5
        reasons.append(f"Niche match: {lead_category}")

    # ── Negative signals ──
    if is_blacklisted:
        score -= 30
        breakdown["blacklisted"] = -30
        reasons.append("Email or domain is blacklisted")

    if recently_contacted:
        score -= 20
        breakdown["recently_contacted"] = -20
        reasons.append("Already contacted in the last 30 days")

    # Clamp to 0
    final_score = max(score, 0)

    result: dict[str, Any] = {
        "lead_id": lead["id"],
        "final_score": final_score,
        "breakdown": breakdown,
        "reasons": reasons,
    }

    logger.info(
        "lead_scored",
        lead_id=lead["id"],
        business=lead.get("business_name"),
        score=final_score,
        reasons=reasons,
    )
    return result
