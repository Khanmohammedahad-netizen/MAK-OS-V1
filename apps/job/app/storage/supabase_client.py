"""Supabase client — all database operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from supabase import Client, create_client

from app.config import Settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class SupabaseStore:
    """Thin wrapper around Supabase client for typed CRUD operations."""

    def __init__(self, settings: Settings) -> None:
        self._client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )

    # ── Leads ──

    def upsert_lead(self, lead: dict[str, Any]) -> dict[str, Any] | None:
        """Insert or skip a lead based on dedupe_key. Returns the row if new."""
        result = (
            self._client.table("leads")
            .upsert(lead, on_conflict="dedupe_key", ignore_duplicates=True)
            .execute()
        )
        if result.data:
            return result.data[0]  # type: ignore[no-any-return]
        return None

    def get_leads_by_status(self, status: str, limit: int = 200) -> list[dict[str, Any]]:
        """Fetch leads filtered by status."""
        result = (
            self._client.table("leads")
            .select("*")
            .eq("status", status)
            .limit(limit)
            .execute()
        )
        return result.data  # type: ignore[no-any-return]

    def get_leads_by_country_and_status(
        self, country: str, status: str, limit: int = 200
    ) -> list[dict[str, Any]]:
        """Fetch leads filtered by country and status."""
        result = (
            self._client.table("leads")
            .select("*")
            .eq("country", country)
            .eq("status", status)
            .limit(limit)
            .execute()
        )
        return result.data  # type: ignore[no-any-return]

    def update_lead_status(self, lead_id: str, status: str) -> None:
        """Update a single lead's status."""
        self._client.table("leads").update({"status": status}).eq("id", lead_id).execute()

    def get_top_scored_leads(self, threshold: int, limit: int) -> list[dict[str, Any]]:
        """Get top scored leads that are ready for outreach."""
        result = (
            self._client.table("scores")
            .select("*, leads(*)")
            .gte("final_score", threshold)
            .order("final_score", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data  # type: ignore[no-any-return]

    def get_scored_leads_for_queue(self, threshold: int, limit: int) -> list[dict[str, Any]]:
        """Get leads with status='scored' and score >= threshold, not blacklisted."""
        result = (
            self._client.table("leads")
            .select("*, scores(*)")
            .eq("status", "scored")
            .limit(limit * 3)
            .execute()
        )
        qualified: list[dict[str, Any]] = []
        for lead in result.data:
            scores = lead.get("scores", [])
            if not scores:
                continue
            score_row = scores[0] if isinstance(scores, list) else scores
            if score_row.get("final_score", 0) >= threshold:
                lead["_score"] = score_row
                qualified.append(lead)
        qualified.sort(key=lambda x: x["_score"]["final_score"], reverse=True)
        return qualified[:limit]

    # ── Enrichment ──

    def insert_enrichment(self, enrichment: dict[str, Any]) -> None:
        """Insert Companies House enrichment row."""
        self._client.table("enrichment_companies_house").upsert(
            enrichment, on_conflict="lead_id", ignore_duplicates=True
        ).execute()

    def get_enrichment(self, lead_id: str) -> dict[str, Any] | None:
        """Get enrichment for a lead."""
        result = (
            self._client.table("enrichment_companies_house")
            .select("*")
            .eq("lead_id", lead_id)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    # ── Audits ──

    def insert_audit(self, audit: dict[str, Any]) -> None:
        """Insert audit result row."""
        self._client.table("audits").insert(audit).execute()

    def get_audit(self, lead_id: str) -> dict[str, Any] | None:
        """Get latest audit for a lead."""
        result = (
            self._client.table("audits")
            .select("*")
            .eq("lead_id", lead_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    # ── Scores ──

    def insert_score(self, score: dict[str, Any]) -> None:
        """Insert score row."""
        self._client.table("scores").insert(score).execute()

    # ── Drafts ──

    def insert_draft(self, draft: dict[str, Any]) -> None:
        """Insert draft row."""
        self._client.table("drafts").insert(draft).execute()

    def get_draft(self, lead_id: str) -> dict[str, Any] | None:
        """Get latest draft for a lead."""
        result = (
            self._client.table("drafts")
            .select("*")
            .eq("lead_id", lead_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None

    def approve_draft(self, draft_id: str) -> None:
        """Mark a draft as approved."""
        self._client.table("drafts").update({"approved": True}).eq("id", draft_id).execute()

    # ── Outreach Logs ──

    def insert_outreach_log(self, log_entry: dict[str, Any]) -> None:
        """Insert outreach log entry."""
        self._client.table("outreach_logs").insert(log_entry).execute()

    def get_recent_outreach(self, lead_id: str, days: int = 30) -> list[dict[str, Any]]:
        """Check if lead was contacted recently."""
        from datetime import timedelta

        cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=days)).isoformat()
        result = (
            self._client.table("outreach_logs")
            .select("*")
            .eq("lead_id", lead_id)
            .gte("created_at", cutoff)
            .execute()
        )
        return result.data  # type: ignore[no-any-return]

    # ── Blacklist ──

    def is_blacklisted(self, email: str | None, domain: str | None = None) -> bool:
        """Check if an email or domain is blacklisted."""
        if email:
            result = (
                self._client.table("blacklist")
                .select("id")
                .eq("email", email)
                .limit(1)
                .execute()
            )
            if result.data:
                return True
        if domain:
            result = (
                self._client.table("blacklist")
                .select("id")
                .eq("domain", domain)
                .limit(1)
                .execute()
            )
            if result.data:
                return True
        return False

    # ── Pipeline Runs ──

    def create_pipeline_run(self) -> str:
        """Create a new pipeline run and return its ID."""
        run_id = str(uuid4())
        self._client.table("pipeline_runs").insert(
            {"id": run_id, "status": "running", "metrics": {}}
        ).execute()
        return run_id

    def finish_pipeline_run(
        self,
        run_id: str,
        status: str,
        metrics: dict[str, Any],
    ) -> None:
        """Finalize a pipeline run with status and metrics."""
        self._client.table("pipeline_runs").update(
            {
                "finished_at": datetime.now(tz=timezone.utc).isoformat(),
                "status": status,
                "metrics": metrics,
            }
        ).eq("id", run_id).execute()
