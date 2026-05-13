"""Jinja template-based email writer — deterministic fallback.

Used when Gemini is rate-limited, down, or returns unparseable output.
Niche-specific templates with direct, founder-to-founder tone.
"""

from __future__ import annotations

from typing import Any

from jinja2 import Environment, BaseLoader

from app.utils.logging import get_logger

logger = get_logger(__name__)

# ── Templates keyed by niche ──

TEMPLATES: dict[str, dict[str, str]] = {
    "restaurants": {
        "subject": "{{ business_name }} — quick website note",
        "body": """Hi,

I checked {{ business_name }}'s website and spotted a gap: {{ weakness }}. For a restaurant in {{ city }}, that means lost covers every week.

We build booking-ready sites and ordering systems for restaurants — fixed price, live in 10 days.

Worth a 10-min call this week?

Ahad Khan — MAK Software Solutions""",
    },
    "salons_clinics": {
        "subject": "{{ business_name }} — booking idea",
        "body": """Hi,

Had a look at {{ business_name }}'s online setup. {{ weakness }}. Most salons and clinics we work with lose 20-30%% of walk-ins because there is no simple way to book online.

We set up automated booking + reminders that work from day one — no monthly subscription.

Worth a quick 10-min call?

Ahad Khan — MAK Software Solutions""",
    },
    "trades_services": {
        "subject": "{{ business_name }} — getting found online",
        "body": """Hi,

I looked at {{ business_name }}'s web presence. {{ weakness }}. When someone in {{ city }} searches for your trade, you are probably not showing up.

We build fast, mobile-first sites with quote request forms — one-time cost, you own everything.

Worth a 10-min call to see if it fits?

Ahad Khan — MAK Software Solutions""",
    },
    "generic_smb": {
        "subject": "{{ business_name }} — spotted something",
        "body": """Hi,

Quick note on {{ business_name }}: {{ weakness }}. That is fixable and it is costing you customers.

We help small businesses in {{ city }} get a proper web presence — site, forms, automation — at a fixed price.

Happy to walk through it in a 10-min call if useful.

Ahad Khan — MAK Software Solutions""",
    },
}

# Map config niche values to template keys
NICHE_TO_TEMPLATE: dict[str, str] = {
    "restaurant": "restaurants",
    "salon": "salons_clinics",
    "clinic": "salons_clinics",
    "trades": "trades_services",
    "generic": "generic_smb",
}


def _pick_template(niche: str, category: str) -> dict[str, str]:
    """Select the best template for the given niche/category."""
    # Try exact niche match first
    template_key = NICHE_TO_TEMPLATE.get(niche.lower())
    if template_key and template_key in TEMPLATES:
        return TEMPLATES[template_key]

    # Try category-based matching
    cat_lower = category.lower() if category else ""
    if any(kw in cat_lower for kw in ("restaurant", "cafe", "fast_food", "food")):
        return TEMPLATES["restaurants"]
    if any(kw in cat_lower for kw in ("hair", "beauty", "salon", "dentist", "doctor", "clinic")):
        return TEMPLATES["salons_clinics"]
    if any(kw in cat_lower for kw in ("plumb", "electric", "carpenter", "trade", "builder")):
        return TEMPLATES["trades_services"]

    return TEMPLATES["generic_smb"]


def _pick_weakness(weakness_summary: str) -> str:
    """Extract the most impactful weakness from the summary."""
    if not weakness_summary or weakness_summary == "No major issues found":
        return "your website could use a refresh to convert more visitors"

    weaknesses = [w.strip() for w in weakness_summary.split(";") if w.strip()]

    # Priority order for mentioning
    priority = [
        "No online booking",
        "No contact form",
        "Not mobile-optimised",
        "No HTTPS",
        "No clear call-to-action",
        "generic email",
    ]
    for p in priority:
        for w in weaknesses:
            if p.lower() in w.lower():
                return w.lower()

    return weaknesses[0].lower() if weaknesses else "your website has room for improvement"


def generate_email_template(
    business_name: str,
    category: str,
    city: str,
    weakness_summary: str,
    niche: str,
) -> dict[str, str]:
    """Generate a cold email using Jinja templates.

    Always succeeds — this is the deterministic fallback.

    Returns:
        {"subject": "...", "body": "..."}
    """
    template_pair = _pick_template(niche, category)
    weakness = _pick_weakness(weakness_summary)

    env = Environment(loader=BaseLoader())

    context = {
        "business_name": business_name,
        "city": city or "your area",
        "weakness": weakness,
        "category": category or niche,
    }

    subject = env.from_string(template_pair["subject"]).render(**context)
    body = env.from_string(template_pair["body"]).render(**context)

    # Ensure subject fits 55 char limit
    if len(subject) > 55:
        subject = subject[:52] + "..."

    logger.info("template_generated", business=business_name, niche=niche)
    return {"subject": subject, "body": body}
