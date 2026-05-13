"""Tests for app.scoring.rule_engine module."""

from app.scoring.rule_engine import score_lead


def _make_lead(**overrides: object) -> dict:  # type: ignore[type-arg]
    base = {
        "id": "test-lead-001",
        "business_name": "Test Restaurant",
        "website": "https://testrestaurant.com",
        "email": "info@testrestaurant.com",
        "phone": "+441234567890",
        "city": "London",
        "country": "GB",
        "category": "restaurant",
    }
    base.update(overrides)
    return base


def _make_audit(**overrides: object) -> dict:  # type: ignore[type-arg]
    base = {
        "reachable": True,
        "https": True,
        "has_title": True,
        "has_meta_desc": True,
        "has_viewport": True,
        "has_contact_form": True,
        "has_cta": True,
        "has_booking": True,
        "has_whatsapp": False,
        "generic_email": False,
        "weakness_summary": "No major issues found",
        "audit_score": 0,
    }
    base.update(overrides)
    return base


class TestScoreLead:
    def test_perfect_site_scores_low(self) -> None:
        lead = _make_lead()
        audit = _make_audit()
        result = score_lead(lead, audit, None, False, False, "restaurant")
        # Only niche match bonus expected
        assert result["final_score"] <= 10

    def test_no_booking_adds_20(self) -> None:
        lead = _make_lead()
        audit = _make_audit(has_booking=False)
        result = score_lead(lead, audit, None, False, False, "restaurant")
        assert result["breakdown"].get("no_booking_cta") == 20
        assert "No online booking" in result["reasons"][0]

    def test_no_contact_form_adds_15(self) -> None:
        lead = _make_lead()
        audit = _make_audit(has_contact_form=False)
        result = score_lead(lead, audit, None, False, False, "restaurant")
        assert result["breakdown"].get("no_contact_form") == 15

    def test_generic_email_adds_15(self) -> None:
        lead = _make_lead()
        audit = _make_audit(generic_email=True)
        result = score_lead(lead, audit, None, False, False, "restaurant")
        assert result["breakdown"].get("generic_email") == 15

    def test_no_viewport_adds_10(self) -> None:
        lead = _make_lead()
        audit = _make_audit(has_viewport=False)
        result = score_lead(lead, audit, None, False, False, "restaurant")
        assert result["breakdown"].get("no_mobile_viewport") == 10

    def test_no_https_adds_10(self) -> None:
        lead = _make_lead()
        audit = _make_audit(https=False)
        result = score_lead(lead, audit, None, False, False, "restaurant")
        assert result["breakdown"].get("no_https") == 10

    def test_ch_active_adds_10(self) -> None:
        lead = _make_lead()
        audit = _make_audit()
        enrichment = {"company_status": "active"}
        result = score_lead(lead, audit, enrichment, False, False, "restaurant")
        assert result["breakdown"].get("ch_active") == 10

    def test_blacklisted_subtracts_30(self) -> None:
        lead = _make_lead()
        audit = _make_audit(has_booking=False, has_contact_form=False)
        result = score_lead(lead, audit, None, True, False, "restaurant")
        assert result["breakdown"].get("blacklisted") == -30

    def test_recently_contacted_subtracts_20(self) -> None:
        lead = _make_lead()
        audit = _make_audit()
        result = score_lead(lead, audit, None, False, True, "restaurant")
        assert result["breakdown"].get("recently_contacted") == -20

    def test_no_website_scores_25(self) -> None:
        lead = _make_lead(website=None)
        result = score_lead(lead, None, None, False, False, "restaurant")
        assert result["breakdown"].get("no_website") == 25

    def test_all_weaknesses_max_score(self) -> None:
        lead = _make_lead()
        audit = _make_audit(
            has_booking=False,
            has_contact_form=False,
            generic_email=True,
            has_viewport=False,
            https=False,
        )
        enrichment = {"company_status": "active"}
        result = score_lead(lead, audit, enrichment, False, False, "restaurant")
        expected = 20 + 15 + 15 + 10 + 10 + 10 + 5
        assert result["final_score"] == expected

    def test_score_never_negative(self) -> None:
        lead = _make_lead()
        audit = _make_audit()
        result = score_lead(lead, audit, None, True, True, "restaurant")
        assert result["final_score"] >= 0

    def test_niche_match_adds_5(self) -> None:
        lead = _make_lead(category="restaurant")
        audit = _make_audit()
        result = score_lead(lead, audit, None, False, False, "restaurant")
        assert result["breakdown"].get("niche_match") == 5
