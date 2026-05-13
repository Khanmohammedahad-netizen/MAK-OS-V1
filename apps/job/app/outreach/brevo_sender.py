"""Brevo transactional email sender — free tier (300/day, we cap at 30).

Uses Brevo's v3 SMTP API to send emails and track message IDs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.utils.logging import get_logger
from app.utils.retry import with_retry

logger = get_logger(__name__)

BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"


@with_retry(max_attempts=3, min_wait=2.0, max_wait=10.0)
def send_email(
    api_key: str,
    sender_email: str,
    sender_name: str,
    to_email: str,
    subject: str,
    body: str,
) -> dict[str, Any]:
    """Send a transactional email via Brevo.

    Args:
        api_key: Brevo API key.
        sender_email: From email address.
        sender_name: From display name.
        to_email: Recipient email.
        subject: Email subject line.
        body: Email body (plain text).

    Returns:
        Dict with brevo_message_id, status, and sent_at.

    Raises:
        httpx.HTTPStatusError: On Brevo API error (after retries).
    """
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": to_email}],
        "subject": subject,
        "textContent": body,
    }

    with httpx.Client(timeout=15.0) as client:
        resp = client.post(BREVO_SEND_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    message_id = data.get("messageId", "")

    logger.info(
        "email_sent",
        to=to_email,
        subject=subject[:50],
        message_id=message_id,
    )

    return {
        "brevo_message_id": message_id,
        "status": "sent",
        "sent_at": datetime.now(tz=timezone.utc).isoformat(),
    }
