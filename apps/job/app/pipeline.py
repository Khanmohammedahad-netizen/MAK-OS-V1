"""Daily pipeline orchestrator — the core of MAK Lead Engine.

Executes the 10-step daily sequence:
1. Load config
2. Scrape leads (Overpass → Google Places → Yelp)
3. Normalize + dedupe
4. Enrich (UK only, Companies House)
5. Audit websites
6. Score leads
7. Queue top N
8. Generate drafts (Gemini → template fallback)
9. Send via Brevo (skip if DRY_RUN)
10. Write run summary
"""

from __future__ import annotations

from typing import Any

from app.audit.website_audit import audit_website
from app.config import Settings
from app.enrichment.companies_house import enrich_companies_house
from app.outreach.brevo_sender import send_email
from app.personalization.gemini_writer import generate_email_gemini
from app.personalization.template_writer import generate_email_template
from app.scoring.rule_engine import score_lead
from app.sources.google_places import enrich_via_places
from app.sources.overpass import scrape_overpass
from app.sources.yelp import search_yelp
from app.storage.supabase_client import SupabaseStore
from app.utils.dedupe import compute_dedupe_key
from app.utils.logging import get_logger

logger = get_logger(__name__)


class PipelineMetrics:
    """Mutable counters for the pipeline run."""

    def __init__(self) -> None:
        self.leads_scraped: int = 0
        self.leads_new: int = 0
        self.leads_enriched: int = 0
        self.leads_audited: int = 0
        self.leads_scored: int = 0
        self.leads_queued: int = 0
        self.emails_sent: int = 0
        self.errors: int = 0

    def to_dict(self) -> dict[str, int]:
        """Serialize to JSON-compatible dict."""
        return {
            "leads_scraped": self.leads_scraped,
            "leads_new": self.leads_new,
            "leads_enriched": self.leads_enriched,
            "leads_audited": self.leads_audited,
            "leads_scored": self.leads_scored,
            "leads_queued": self.leads_queued,
            "emails_sent": self.emails_sent,
            "errors": self.errors,
        }


def run_daily_pipeline(settings: Settings) -> dict[str, Any]:
    """Execute the full daily pipeline.

    Returns:
        Dict with run_id, status, and metrics.
    """
    store = SupabaseStore(settings)
    metrics = PipelineMetrics()
    run_id = store.create_pipeline_run()

    logger.info("pipeline_start", run_id=run_id, niche=settings.target_niche)

    try:
        # ── Step 1: Load config (already in settings) ──
        bbox = settings.bbox_tuple

        # ── Step 2: Scrape ──
        raw_leads = _step_scrape(settings, bbox)
        metrics.leads_scraped = len(raw_leads)

        # ── Step 3: Normalize + Dedupe + Upsert ──
        new_leads = _step_dedupe_and_upsert(store, raw_leads, settings)
        metrics.leads_new = len(new_leads)

        # ── Step 4: Enrich (UK only) ──
        enriched_count = _step_enrich(store, new_leads, settings)
        metrics.leads_enriched = enriched_count

        # ── Step 5: Audit ──
        audited_count = _step_audit(store, new_leads, metrics)
        metrics.leads_audited = audited_count

        # ── Step 6: Score ──
        scored_count = _step_score(store, new_leads, settings, metrics)
        metrics.leads_scored = scored_count

        # ── Step 7: Queue top N ──
        queued_leads = _step_queue(store, settings)
        metrics.leads_queued = len(queued_leads)

        # ── Step 8: Generate drafts ──
        _step_generate_drafts(store, queued_leads, settings, metrics)

        # ── Step 9: Send via Brevo ──
        if not settings.dry_run:
            sent_count = _step_send(store, queued_leads, settings, metrics)
            metrics.emails_sent = sent_count
        else:
            logger.info("pipeline_dry_run", message="Skipping email send")

        # ── Step 10: Write run summary ──
        store.finish_pipeline_run(run_id, "completed", metrics.to_dict())
        logger.info("pipeline_complete", run_id=run_id, metrics=metrics.to_dict())

    except Exception as exc:
        metrics.errors += 1
        logger.error("pipeline_failed", run_id=run_id, error=str(exc))
        store.finish_pipeline_run(run_id, "failed", metrics.to_dict())
        raise

    return {"run_id": run_id, "status": "completed", "metrics": metrics.to_dict()}


def _step_scrape(
    settings: Settings, bbox: tuple[float, float, float, float]
) -> list[dict[str, Any]]:
    """Step 2: Scrape leads from all enabled sources."""
    leads: list[dict[str, Any]] = []

    # Primary: Overpass
    try:
        overpass_leads = scrape_overpass(
            bbox=bbox,
            niche=settings.target_niche,
            cap=settings.lead_scrape_cap,
        )
        leads.extend(overpass_leads)
        logger.info("scrape_overpass", count=len(overpass_leads))
    except Exception as exc:
        logger.error("scrape_overpass_failed", error=str(exc))

    # If Overpass didn't fill the cap, try Yelp
    remaining = settings.lead_scrape_cap - len(leads)
    if remaining > 0 and settings.yelp_api_key:
        try:
            yelp_leads = search_yelp(
                niche=settings.target_niche,
                city=settings.target_city,
                api_key=settings.yelp_api_key,
                limit=min(remaining, 20),
            )
            leads.extend(yelp_leads)
            logger.info("scrape_yelp", count=len(yelp_leads))
        except Exception as exc:
            logger.error("scrape_yelp_failed", error=str(exc))

    return leads[: settings.lead_scrape_cap]


def _step_dedupe_and_upsert(
    store: SupabaseStore,
    raw_leads: list[dict[str, Any]],
    settings: Settings,
) -> list[dict[str, Any]]:
    """Step 3: Normalize, compute dedupe key, and upsert. Returns new leads only."""
    new_leads: list[dict[str, Any]] = []

    for lead in raw_leads:
        # Fill in country if missing
        if not lead.get("country"):
            lead["country"] = settings.target_country

        # Compute dedupe key
        lead["dedupe_key"] = compute_dedupe_key(
            website=lead.get("website"),
            phone=lead.get("phone"),
            business_name=lead.get("business_name"),
        )

        # Enrich missing fields via Google Places
        if settings.google_maps_api_key and (not lead.get("website") or not lead.get("phone")):
            try:
                enrichment = enrich_via_places(
                    business_name=lead.get("business_name", ""),
                    city=lead.get("city") or settings.target_city,
                    api_key=settings.google_maps_api_key,
                )
                if enrichment:
                    if not lead.get("website") and enrichment.get("website"):
                        lead["website"] = enrichment["website"]
                    if not lead.get("phone") and enrichment.get("phone"):
                        lead["phone"] = enrichment["phone"]
                    if not lead.get("address") and enrichment.get("address"):
                        lead["address"] = enrichment["address"]
            except Exception as exc:
                logger.warning("places_enrich_failed", error=str(exc))

        result = store.upsert_lead(lead)
        if result:
            new_leads.append(result)

    logger.info("dedupe_complete", total=len(raw_leads), new=len(new_leads))
    return new_leads


def _step_enrich(
    store: SupabaseStore,
    leads: list[dict[str, Any]],
    settings: Settings,
) -> int:
    """Step 4: Enrich UK leads via Companies House."""
    enriched = 0
    if not settings.companies_house_api_key:
        return enriched

    uk_leads = [l for l in leads if (l.get("country") or "").upper() == "GB"]
    for lead in uk_leads:
        try:
            enrichment = enrich_companies_house(
                business_name=lead["business_name"],
                lead_id=lead["id"],
                api_key=settings.companies_house_api_key,
            )
            if enrichment:
                store.insert_enrichment(enrichment)
                store.update_lead_status(lead["id"], "enriched")
                enriched += 1
        except Exception as exc:
            logger.warning("ch_enrich_failed", lead_id=lead["id"], error=str(exc))

    return enriched


def _step_audit(
    store: SupabaseStore,
    leads: list[dict[str, Any]],
    metrics: PipelineMetrics,
) -> int:
    """Step 5: Audit each lead's website."""
    audited = 0
    for lead in leads:
        website = lead.get("website")
        if not website:
            continue
        try:
            audit_result = audit_website(
                lead_id=lead["id"],
                website=website,
                email=lead.get("email"),
            )
            store.insert_audit(audit_result)
            store.update_lead_status(lead["id"], "audited")
            audited += 1
        except Exception as exc:
            logger.warning("audit_failed", lead_id=lead["id"], error=str(exc))
            metrics.errors += 1

    return audited


def _step_score(
    store: SupabaseStore,
    leads: list[dict[str, Any]],
    settings: Settings,
    metrics: PipelineMetrics,
) -> int:
    """Step 6: Score each lead using the rule engine."""
    scored = 0
    for lead in leads:
        try:
            audit = store.get_audit(lead["id"])
            enrichment = store.get_enrichment(lead["id"]) if lead.get("country") == "GB" else None
            is_blacklisted = store.is_blacklisted(lead.get("email"), None)
            recent_outreach = store.get_recent_outreach(lead["id"], days=30)
            recently_contacted = len(recent_outreach) > 0

            score_result = score_lead(
                lead=lead,
                audit=audit,
                enrichment=enrichment,
                is_blacklisted=is_blacklisted,
                recently_contacted=recently_contacted,
                target_niche=settings.target_niche,
            )
            store.insert_score(score_result)
            store.update_lead_status(lead["id"], "scored")
            scored += 1
        except Exception as exc:
            logger.warning("score_failed", lead_id=lead["id"], error=str(exc))
            metrics.errors += 1

    return scored


def _step_queue(store: SupabaseStore, settings: Settings) -> list[dict[str, Any]]:
    """Step 7: Select top N scored leads for outreach."""
    qualified = store.get_scored_leads_for_queue(
        threshold=settings.score_threshold,
        limit=settings.email_daily_cap,
    )

    # Filter out leads without email
    with_email = [l for l in qualified if l.get("email")]

    for lead in with_email:
        store.update_lead_status(lead["id"], "queued")

    logger.info("queue_complete", qualified=len(qualified), with_email=len(with_email))
    return with_email


def _step_generate_drafts(
    store: SupabaseStore,
    leads: list[dict[str, Any]],
    settings: Settings,
    metrics: PipelineMetrics,
) -> None:
    """Step 8: Generate personalized email drafts for each queued lead."""
    for lead in leads:
        try:
            audit = store.get_audit(lead["id"])
            score_data = lead.get("_score", {})
            weakness_summary = audit.get("weakness_summary", "") if audit else ""
            top_reasons = score_data.get("reasons", [])[:2]

            # Try Gemini first
            email_data = generate_email_gemini(
                api_key=settings.gemini_api_key,
                business_name=lead["business_name"],
                category=lead.get("category", ""),
                city=lead.get("city", settings.target_city),
                weakness_summary=weakness_summary,
                top_reasons=top_reasons,
            )
            generator = "gemini"

            # Fallback to template
            if email_data is None:
                email_data = generate_email_template(
                    business_name=lead["business_name"],
                    category=lead.get("category", ""),
                    city=lead.get("city", settings.target_city),
                    weakness_summary=weakness_summary,
                    niche=settings.target_niche,
                )
                generator = "template"

            draft = {
                "lead_id": lead["id"],
                "subject": email_data["subject"],
                "body": email_data["body"],
                "generator": generator,
                "approved": settings.auto_approve,
            }
            store.insert_draft(draft)

        except Exception as exc:
            logger.warning("draft_failed", lead_id=lead["id"], error=str(exc))
            metrics.errors += 1


def _step_send(
    store: SupabaseStore,
    leads: list[dict[str, Any]],
    settings: Settings,
    metrics: PipelineMetrics,
) -> int:
    """Step 9: Send approved drafts via Brevo."""
    sent_count = 0

    for lead in leads:
        if sent_count >= settings.email_daily_cap:
            break

        draft = store.get_draft(lead["id"])
        if not draft or not draft.get("approved"):
            continue

        to_email = lead.get("email")
        if not to_email:
            continue

        # Check blacklist before sending
        if store.is_blacklisted(to_email):
            store.update_lead_status(lead["id"], "blacklisted")
            continue

        try:
            result = send_email(
                api_key=settings.brevo_api_key,
                sender_email=settings.brevo_sender_email,
                sender_name=settings.brevo_sender_name,
                to_email=to_email,
                subject=draft["subject"],
                body=draft["body"],
            )

            outreach_log = {
                "lead_id": lead["id"],
                "subject": draft["subject"],
                "body": draft["body"],
                "brevo_message_id": result.get("brevo_message_id", ""),
                "status": "sent",
                "sent_at": result.get("sent_at"),
            }
            store.insert_outreach_log(outreach_log)
            store.update_lead_status(lead["id"], "sent")
            sent_count += 1

        except Exception as exc:
            logger.error("send_failed", lead_id=lead["id"], error=str(exc))
            outreach_log = {
                "lead_id": lead["id"],
                "subject": draft["subject"],
                "body": draft["body"],
                "brevo_message_id": "",
                "status": "failed",
                "sent_at": None,
            }
            store.insert_outreach_log(outreach_log)
            metrics.errors += 1

    return sent_count
