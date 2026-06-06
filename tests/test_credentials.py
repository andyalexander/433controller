"""Tests for credential encoding used in the login URL."""
import base64
from urllib.parse import unquote_plus

import pytest

from custom_components.draytek_dsl.coordinator import _encode_credential


def _roundtrip(encoded: str) -> str:
    """Reverse _encode_credential: URL-decode then base64-decode."""
    return base64.b64decode(unquote_plus(encoded)).decode()


class TestEncodeCredential:
    def test_simple_username_roundtrips(self):
        assert _roundtrip(_encode_credential("admin")) == "admin"

    def test_simple_password_roundtrips(self):
        assert _roundtrip(_encode_credential("secret123")) == "secret123"

    def test_special_characters_roundtrip(self):
        password = "P@ss!w0rd#$%"
        assert _roundtrip(_encode_credential(password)) == password

    def test_unicode_password_roundtrips(self):
        password = "pässwörD"
        assert _roundtrip(_encode_credential(password)) == password

    def test_output_is_url_safe(self):
        """Result must not contain raw '+' or '/' that would break a query string."""
        encoded = _encode_credential("user+name/test")
        # URL-encoded characters use %, not raw +/=// in the value position
        assert "/" not in encoded
        # A raw unencoded + would be ambiguous in a query string
        assert "+" not in encoded

    def test_empty_string_roundtrips(self):
        assert _roundtrip(_encode_credential("")) == ""
