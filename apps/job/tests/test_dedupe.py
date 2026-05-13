"""Tests for app.utils.dedupe module."""

from app.utils.dedupe import compute_dedupe_key, normalize_domain, normalize_phone, slugify


class TestNormalizeDomain:
    def test_strips_protocol_and_www(self) -> None:
        assert normalize_domain("https://www.example.com") == "example.com"

    def test_handles_http(self) -> None:
        assert normalize_domain("http://example.com") == "example.com"

    def test_handles_bare_domain(self) -> None:
        assert normalize_domain("example.com") == "example.com"

    def test_strips_trailing_slash(self) -> None:
        assert normalize_domain("https://example.com/") == "example.com"

    def test_lowercases(self) -> None:
        assert normalize_domain("HTTPS://WWW.Example.COM") == "example.com"

    def test_returns_empty_for_none(self) -> None:
        assert normalize_domain(None) == ""

    def test_returns_empty_for_empty_string(self) -> None:
        assert normalize_domain("") == ""

    def test_preserves_subdomain(self) -> None:
        assert normalize_domain("https://shop.example.com") == "shop.example.com"


class TestNormalizePhone:
    def test_strips_non_digits(self) -> None:
        assert normalize_phone("+44 (0) 7911-123456") == "4407911123456"

    def test_returns_empty_for_none(self) -> None:
        assert normalize_phone(None) == ""

    def test_handles_clean_number(self) -> None:
        assert normalize_phone("07911123456") == "07911123456"


class TestSlugify:
    def test_basic_slug(self) -> None:
        assert slugify("The Best Restaurant") == "the-best-restaurant"

    def test_strips_special_chars(self) -> None:
        assert slugify("Mario's Pizza & Pasta!") == "marios-pizza--pasta"

    def test_returns_empty_for_none(self) -> None:
        assert slugify(None) == ""

    def test_collapses_whitespace(self) -> None:
        assert slugify("  too   many   spaces  ") == "too-many-spaces"


class TestComputeDedupeKey:
    def test_deterministic(self) -> None:
        key1 = compute_dedupe_key("https://example.com", "+44 123", "Test Biz")
        key2 = compute_dedupe_key("https://example.com", "+44 123", "Test Biz")
        assert key1 == key2

    def test_different_inputs_different_keys(self) -> None:
        key1 = compute_dedupe_key("example.com", "123", "Test")
        key2 = compute_dedupe_key("other.com", "456", "Other")
        assert key1 != key2

    def test_normalizes_before_hashing(self) -> None:
        key1 = compute_dedupe_key("https://www.example.com/", "(123) 456", "Test Biz")
        key2 = compute_dedupe_key("http://example.com", "123456", "test biz")
        assert key1 == key2

    def test_handles_all_none(self) -> None:
        key = compute_dedupe_key(None, None, None)
        assert isinstance(key, str)
        assert len(key) == 64  # SHA-256 hex digest length
