"""Tests for app.audit.website_audit module — uses offline HTML fixtures."""

from app.audit.website_audit import audit_website, _is_generic_email, _check_text_for_keywords
from unittest.mock import patch, MagicMock


MINIMAL_HTML = """<!DOCTYPE html>
<html>
<head><title>Test Page</title></head>
<body><p>Hello world</p></body>
</html>"""

FULL_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Best Restaurant London</title>
    <meta name="description" content="We serve great food">
    <meta name="viewport" content="width=device-width">
</head>
<body>
    <h1>Welcome</h1>
    <form><input name="email"><textarea name="message"></textarea></form>
    <a href="https://wa.me/123">WhatsApp</a>
    <button>Book a table</button>
    <a href="/order">Order online</a>
</body>
</html>"""

WEAK_HTML = """<!DOCTYPE html>
<html>
<head></head>
<body><p>Coming soon</p></body>
</html>"""


class TestIsGenericEmail:
    def test_gmail(self) -> None:
        assert _is_generic_email("test@gmail.com") is True

    def test_outlook(self) -> None:
        assert _is_generic_email("test@outlook.com") is True

    def test_business_email(self) -> None:
        assert _is_generic_email("info@mybusiness.com") is False

    def test_none(self) -> None:
        assert _is_generic_email(None) is False


class TestCheckTextForKeywords:
    def test_finds_keyword(self) -> None:
        assert _check_text_for_keywords("Book a table now", ["book", "reserve"]) is True

    def test_no_match(self) -> None:
        assert _check_text_for_keywords("Hello world", ["book", "reserve"]) is False

    def test_case_insensitive(self) -> None:
        assert _check_text_for_keywords("BOOK NOW", ["book"]) is True


class TestAuditWebsite:
    @patch("app.audit.website_audit._fetch_page")
    def test_full_site_scores_well(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = (FULL_HTML, True, "https://example.com")
        result = audit_website("lead-1", "https://example.com", "info@business.com")

        assert result["reachable"] is True
        assert result["https"] is True
        assert result["has_title"] is True
        assert result["has_meta_desc"] is True
        assert result["has_viewport"] is True
        assert result["has_contact_form"] is True
        assert result["has_booking"] is True
        assert result["has_whatsapp"] is True
        assert result["generic_email"] is False

    @patch("app.audit.website_audit._fetch_page")
    def test_weak_site_finds_weaknesses(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = (WEAK_HTML, False, "http://example.com")
        result = audit_website("lead-2", "http://example.com", "owner@gmail.com")

        assert result["reachable"] is True
        assert result["https"] is False
        assert result["has_title"] is False
        assert result["has_meta_desc"] is False
        assert result["has_viewport"] is False
        assert result["has_contact_form"] is False
        assert result["generic_email"] is True
        assert result["audit_score"] > 0
        assert "No HTTPS" in result["weakness_summary"]

    @patch("app.audit.website_audit._fetch_page")
    def test_unreachable_site(self, mock_fetch: MagicMock) -> None:
        mock_fetch.side_effect = Exception("Connection refused")
        result = audit_website("lead-3", "https://down.example.com")

        assert result["reachable"] is False
        assert "unreachable" in result["weakness_summary"].lower()

    @patch("app.audit.website_audit._fetch_page")
    def test_minimal_html(self, mock_fetch: MagicMock) -> None:
        mock_fetch.return_value = (MINIMAL_HTML, True, "https://example.com")
        result = audit_website("lead-4", "https://example.com")

        assert result["reachable"] is True
        assert result["has_title"] is True
        assert result["has_meta_desc"] is False
        assert result["has_viewport"] is False
