"""Unit tests for DSL status HTML parsing.

Each test class targets a different firmware / page layout variant so we
know which regex patterns cover which real-world output formats.
"""
import pytest

from custom_components.draytek_dsl.coordinator import _parse_speeds


class TestDownstreamParsing:
    def test_down_speed_kbps(self):
        assert _parse_speeds("<td>Down Speed</td><td>80000 Kbps</td>")["download_kbps"] == 80000

    def test_down_speed_lowercase_kbps(self):
        assert _parse_speeds("<td>Down Speed</td><td>76000 kbps</td>")["download_kbps"] == 76000

    def test_downstream_rate_kbps(self):
        assert _parse_speeds("Downstream Rate: 72000 Kbps")["download_kbps"] == 72000

    def test_downstream_actual_rate(self):
        assert _parse_speeds("Downstream Actual Rate: 68000 Kbps")["download_kbps"] == 68000

    def test_ds_actual_rate(self):
        assert _parse_speeds("DS Actual Rate: 80000 Kbps")["download_kbps"] == 80000

    def test_no_unit_suffix_fallback(self):
        # When Kbps unit is missing, the unitless fallback pattern should still match
        assert _parse_speeds("<td>Down Speed</td><td>75000</td>")["download_kbps"] == 75000

    def test_returns_none_when_absent(self):
        assert _parse_speeds("<html>No speeds here</html>")["download_kbps"] is None


class TestUpstreamParsing:
    def test_up_speed_kbps(self):
        assert _parse_speeds("<td>Up Speed</td><td>20000 Kbps</td>")["upload_kbps"] == 20000

    def test_up_speed_lowercase_kbps(self):
        assert _parse_speeds("<td>Up Speed</td><td>18000 kbps</td>")["upload_kbps"] == 18000

    def test_upstream_rate_kbps(self):
        assert _parse_speeds("Upstream Rate: 19000 Kbps")["upload_kbps"] == 19000

    def test_upstream_actual_rate(self):
        assert _parse_speeds("Upstream Actual Rate: 17500 Kbps")["upload_kbps"] == 17500

    def test_us_actual_rate(self):
        assert _parse_speeds("US Actual Rate: 20000 Kbps")["upload_kbps"] == 20000

    def test_no_unit_suffix_fallback(self):
        assert _parse_speeds("<td>Up Speed</td><td>15000</td>")["upload_kbps"] == 15000

    def test_returns_none_when_absent(self):
        assert _parse_speeds("<html>No speeds here</html>")["upload_kbps"] is None


class TestBothSpeeds:
    def test_table_format(self):
        html = """
        <tr><td>Down Speed</td><td>80000 Kbps</td></tr>
        <tr><td>Up Speed</td><td>20000 Kbps</td></tr>
        """
        data = _parse_speeds(html)
        assert data["download_kbps"] == 80000
        assert data["upload_kbps"] == 20000

    def test_colon_label_format(self):
        html = "Down Speed: 75000 Kbps\nUp Speed: 18000 Kbps"
        data = _parse_speeds(html)
        assert data["download_kbps"] == 75000
        assert data["upload_kbps"] == 18000

    def test_realistic_vigor_2862_vdsl_page(self):
        """Mimics the actual DSL status page structure of the Vigor 2862."""
        html = """
        <html><body>
        <table border="1">
          <tr><th>Item</th><th>Value</th></tr>
          <tr><td>State</td><td>SHOWTIME</td></tr>
          <tr><td>Mode</td><td>VDSL2 17a</td></tr>
          <tr><td>Down Speed</td><td>80000 Kbps</td></tr>
          <tr><td>Up Speed</td><td>20000 Kbps</td></tr>
          <tr><td>SNR Margin (Down/Up)</td><td>8.5 / 12.0 dB</td></tr>
          <tr><td>Attenuation (Down/Up)</td><td>14.0 / 6.5 dB</td></tr>
        </table>
        </body></html>
        """
        data = _parse_speeds(html)
        assert data["download_kbps"] == 80000
        assert data["upload_kbps"] == 20000

    def test_realistic_vigor_ds_us_label_format(self):
        """Alternate firmware label style using DS/US prefixes."""
        html = """
        DS Actual Rate:  72448 Kbps
        US Actual Rate:  19200 Kbps
        DS Attainable Rate: 85000 Kbps
        US Attainable Rate: 22000 Kbps
        """
        data = _parse_speeds(html)
        assert data["download_kbps"] == 72448
        assert data["upload_kbps"] == 19200

    def test_empty_html(self):
        data = _parse_speeds("")
        assert data["download_kbps"] is None
        assert data["upload_kbps"] is None

    def test_snr_numbers_are_not_mistaken_for_speeds(self):
        """SNR margin values (e.g. 8.5 dB) must not be captured as speeds."""
        html = """
        <tr><td>Down Speed</td><td>80000 Kbps</td></tr>
        <tr><td>SNR Margin Down</td><td>8</td></tr>
        <tr><td>Up Speed</td><td>20000 Kbps</td></tr>
        <tr><td>SNR Margin Up</td><td>12</td></tr>
        """
        data = _parse_speeds(html)
        assert data["download_kbps"] == 80000
        assert data["upload_kbps"] == 20000
