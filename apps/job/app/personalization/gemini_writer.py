"""Gemini 1.5 Flash email writer — free tier only (15 RPM, 1M tokens/day).

Every call is wrapped in try/except. On rate limit or any error,
returns None so the pipeline falls back to template_writer.
"""

from __future__ import annotations

import json
from typing import Any

import google.generativeai as genai

from app.utils.logging import get_logger

logger = get_logger(__name__)


def _build_prompt(
    business_name: str,
    category: str,
    city: str,
    weakness_summary: str,
    top_reasons: list[str],
) -> str:
    """Build the Gemini prompt for personalized cold email generation."""
    reasons_text = "\n".join(f"- {r}" for r in top_reasons[:2])
    return f"""You are writing a cold outreach email from Ahad Khan at MAK Software Solutions.

Target business: {business_name}
Category: {category}
Location: {city}
Website weaknesses found: {weakness_summary}
Top scoring reasons:
{reasons_text}

Write a short, direct cold email. Rules:
- Subject line: under 55 characters, no emojis, no exclamation marks
- Body: maximum 4 lines
- Mention ONE specific weakness from the audit
- Offer ONE concrete solution (booking system, website rebuild, automation, or dashboard)
- End with a soft CTA like "worth a 10-min call?"
- Sign off as: Ahad Khan — MAK Software Solutions
- Tone: direct, founder-to-founder, no marketing fluff
- Do NOT use phrases like "I hope this finds you well" or "I noticed that"

Return ONLY valid JSON with exactly two keys: "subject" and "body".
No markdown, no code fences, just the JSON object."""


def generate_email_gemini(
    api_key: str,
    business_name: str,
    category: str,
    city: str,
    weakness_summary: str,
    top_reasons: list[str],
) -> dict[str, str] | None:
    """Generate a personalized cold email using Gemini 1.5 Flash.

    Returns {"subject": "...", "body": "..."} on success, None on failure.
    The caller must fall back to template_writer on None.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = _build_prompt(
            business_name=business_name,
            category=category,
            city=city,
            weakness_summary=weakness_summary,
            top_reasons=top_reasons,
        )

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                max_output_tokens=300,
            ),
        )

        if not response.text:
            logger.warning("gemini_empty_response", business=business_name)
            return None

        # Strip markdown code fences if present
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        result: dict[str, str] = json.loads(text)

        if "subject" not in result or "body" not in result:
            logger.warning("gemini_bad_format", raw=text[:200])
            return None

        logger.info("gemini_generated", business=business_name)
        return result

    except json.JSONDecodeError as exc:
        logger.warning("gemini_json_error", error=str(exc))
        return None
    except Exception as exc:
        # Catches 429 rate limit, network errors, quota exhaustion, etc.
        logger.warning("gemini_error", error=str(exc), type=type(exc).__name__)
        return None
