"""MAK Lead Engine — Pydantic Settings (env-driven configuration)."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All configuration is read from environment variables or .env file."""

    # ── Supabase ──
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_service_role_key: str = Field(..., description="Supabase service_role secret key")

    # ── Gemini ──
    gemini_api_key: str = Field(..., description="Google AI Studio API key")

    # ── Brevo ──
    brevo_api_key: str = Field(..., description="Brevo transactional API key")
    brevo_sender_email: str = Field(default="ahad@maksoftware.co")
    brevo_sender_name: str = Field(default="Ahad Khan")

    # ── Google Maps / Places ──
    google_maps_api_key: str = Field(default="", description="Google Maps API key (optional)")

    # ── Yelp ──
    yelp_api_key: str = Field(default="", description="Yelp Fusion API key (optional)")

    # ── Companies House ──
    companies_house_api_key: str = Field(default="", description="UK Companies House API key")

    # ── Apify (optional plugin) ──
    apify_enabled: bool = Field(default=False)
    apify_token: str = Field(default="")

    # ── Pipeline behaviour ──
    lead_scrape_cap: int = Field(default=50, ge=1, le=200)
    email_daily_cap: int = Field(default=30, ge=1, le=300)
    auto_approve: bool = Field(default=True)
    dry_run: bool = Field(default=False)
    score_threshold: int = Field(default=40, ge=0, le=100)

    # ── Targeting ──
    target_niche: str = Field(default="restaurant")
    target_country: str = Field(default="GB")
    target_city: str = Field(default="London")
    target_bbox: str = Field(
        default="51.28,-0.49,51.69,0.24",
        description="Overpass bounding box: south,west,north,east",
    )

    # ── GCP ──
    gcp_project_id: str = Field(default="mak-lead-engine")
    gcp_region: str = Field(default="asia-south1")

    # ── Logging ──
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def bbox_tuple(self) -> tuple[float, float, float, float]:
        """Parse bounding box string into (south, west, north, east)."""
        parts = [float(p.strip()) for p in self.target_bbox.split(",")]
        if len(parts) != 4:
            msg = f"TARGET_BBOX must have 4 comma-separated floats, got {len(parts)}"
            raise ValueError(msg)
        return (parts[0], parts[1], parts[2], parts[3])


def get_settings() -> Settings:
    """Factory for settings — allows test override."""
    return Settings()  # type: ignore[call-arg]
