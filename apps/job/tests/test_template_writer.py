"""Tests for app.personalization.template_writer module."""

from app.personalization.template_writer import generate_email_template, _pick_weakness


class TestPickWeakness:
    def test_no_issues(self) -> None:
        result = _pick_weakness("No major issues found")
        assert "refresh" in result or "improvement" in result

    def test_picks_priority_weakness(self) -> None:
        summary = "No HTTPS; Missing page title; No online booking system"
        result = _pick_weakness(summary)
        assert "no online booking" in result.lower() or "no https" in result.lower()

    def test_empty_summary(self) -> None:
        result = _pick_weakness("")
        assert len(result) > 0

    def test_single_weakness(self) -> None:
        result = _pick_weakness("Not mobile-optimised")
        assert "mobile" in result.lower()


class TestGenerateEmailTemplate:
    def test_restaurant_template(self) -> None:
        result = generate_email_template(
            business_name="Mario's Pizza",
            category="restaurant",
            city="London",
            weakness_summary="No online booking system; No contact form",
            niche="restaurant",
        )
        assert "subject" in result
        assert "body" in result
        assert "Mario's Pizza" in result["subject"]
        assert "Ahad Khan" in result["body"]
        assert len(result["subject"]) <= 55

    def test_salon_template(self) -> None:
        result = generate_email_template(
            business_name="Glow Salon",
            category="hairdresser",
            city="Manchester",
            weakness_summary="No online booking system",
            niche="salon",
        )
        assert "Glow Salon" in result["subject"]
        assert "booking" in result["body"].lower()

    def test_trades_template(self) -> None:
        result = generate_email_template(
            business_name="ABC Plumbing",
            category="plumber",
            city="Birmingham",
            weakness_summary="Not mobile-optimised",
            niche="trades",
        )
        assert "ABC Plumbing" in result["subject"]
        assert "MAK Software" in result["body"]

    def test_generic_fallback(self) -> None:
        result = generate_email_template(
            business_name="Unknown Biz",
            category="other",
            city="Leeds",
            weakness_summary="No HTTPS",
            niche="unknown_niche",
        )
        assert "Unknown Biz" in result["subject"]
        assert "Ahad Khan" in result["body"]

    def test_subject_length_capped(self) -> None:
        result = generate_email_template(
            business_name="A Very Long Business Name That Exceeds The Fifty Five Character Limit",
            category="restaurant",
            city="London",
            weakness_summary="No booking",
            niche="restaurant",
        )
        assert len(result["subject"]) <= 55

    def test_includes_weakness(self) -> None:
        result = generate_email_template(
            business_name="Test Cafe",
            category="cafe",
            city="London",
            weakness_summary="No contact form",
            niche="restaurant",
        )
        assert "contact form" in result["body"].lower() or "weakness" in result["body"].lower() or "form" in result["body"].lower()

    def test_soft_cta_present(self) -> None:
        result = generate_email_template(
            business_name="Test Place",
            category="restaurant",
            city="London",
            weakness_summary="No booking",
            niche="restaurant",
        )
        body_lower = result["body"].lower()
        assert "10-min" in body_lower or "call" in body_lower
