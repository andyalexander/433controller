"""Integration tests against a real DrayTek router.

These tests are skipped automatically unless a .env file (or environment
variables) provides real router credentials:

    DRAYTEK_HOST       Router IP or hostname (required)
    DRAYTEK_PORT       Web interface port (default: 80)
    DRAYTEK_USERNAME   Admin username (default: admin)
    DRAYTEK_PASSWORD   Admin password (required)

Copy .env.example to .env and fill in your values. The .env file is
git-ignored and will never be committed.
"""
from __future__ import annotations

import os
from pathlib import Path

import aiohttp
import pytest

# Load .env if present (silently skip if python-dotenv is not installed)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

_HOST = os.getenv("DRAYTEK_HOST")
_PORT = int(os.getenv("DRAYTEK_PORT", "80"))
_USERNAME = os.getenv("DRAYTEK_USERNAME", "admin")
_PASSWORD = os.getenv("DRAYTEK_PASSWORD")

_router_available = pytest.mark.skipif(
    not _HOST or not _PASSWORD,
    reason="Set DRAYTEK_HOST and DRAYTEK_PASSWORD in .env to run integration tests",
)


@_router_available
async def test_router_is_reachable():
    """Basic connectivity check — the router must respond to HTTP."""
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(
            f"http://{_HOST}:{_PORT}/",
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            assert resp.status in (200, 302, 401), (
                f"Unexpected status {resp.status} — is {_HOST}:{_PORT} the right address?"
            )


@_router_available
async def test_login_succeeds():
    """Login must return HTTP 200 or 302 (redirect to main page)."""
    from custom_components.draytek_dsl.coordinator import _encode_credential

    url = (
        f"http://{_HOST}:{_PORT}/cgi-bin/wlogin.cgi"
        f"?aa={_encode_credential(_USERNAME)}"
        f"&ab={_encode_credential(_PASSWORD)}"
    )
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            assert resp.status in (200, 302), (
                f"Login failed with HTTP {resp.status}. "
                "Check DRAYTEK_USERNAME and DRAYTEK_PASSWORD in .env."
            )


@_router_available
async def test_dsl_speeds_are_returned():
    """After login, at least one DSL status path must return non-zero speeds."""
    from custom_components.draytek_dsl.const import DSL_STATUS_PATHS
    from custom_components.draytek_dsl.coordinator import _encode_credential, _parse_speeds

    base_url = f"http://{_HOST}:{_PORT}"
    connector = aiohttp.TCPConnector(ssl=False)

    async with aiohttp.ClientSession(connector=connector) as session:
        login_url = (
            f"{base_url}/cgi-bin/wlogin.cgi"
            f"?aa={_encode_credential(_USERNAME)}"
            f"&ab={_encode_credential(_PASSWORD)}"
        )
        async with session.get(login_url, timeout=aiohttp.ClientTimeout(total=10)):
            pass

        found_path = None
        data = {"download_kbps": None, "upload_kbps": None}

        for path in DSL_STATUS_PATHS:
            url = f"{base_url}{path}"
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        continue
                    html = await resp.text()
                    data = _parse_speeds(html)
                    if data["download_kbps"] is not None or data["upload_kbps"] is not None:
                        found_path = path
                        break
            except aiohttp.ClientError:
                continue

    assert found_path is not None, (
        f"No DSL speed data found on any of these paths: {DSL_STATUS_PATHS}\n"
        "If your router is connected and synced, open an issue with your firmware "
        "version and the router's Diagnostics > DSL Status page URL."
    )
    assert data["download_kbps"] is not None and data["download_kbps"] > 0, (
        f"Download speed is zero or missing (path: {found_path})"
    )
    assert data["upload_kbps"] is not None and data["upload_kbps"] > 0, (
        f"Upload speed is zero or missing (path: {found_path})"
    )


@_router_available
async def test_dsl_speeds_are_plausible():
    """Speeds must be in a sensible range for VDSL2 (100 kbps – 300 Mbps)."""
    from custom_components.draytek_dsl.const import DSL_STATUS_PATHS
    from custom_components.draytek_dsl.coordinator import _encode_credential, _parse_speeds

    base_url = f"http://{_HOST}:{_PORT}"
    connector = aiohttp.TCPConnector(ssl=False)

    async with aiohttp.ClientSession(connector=connector) as session:
        login_url = (
            f"{base_url}/cgi-bin/wlogin.cgi"
            f"?aa={_encode_credential(_USERNAME)}"
            f"&ab={_encode_credential(_PASSWORD)}"
        )
        async with session.get(login_url, timeout=aiohttp.ClientTimeout(total=10)):
            pass

        for path in DSL_STATUS_PATHS:
            url = f"{base_url}{path}"
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        continue
                    html = await resp.text()
                    data = _parse_speeds(html)
                    if data["download_kbps"] is not None:
                        assert 100 <= data["download_kbps"] <= 300_000, (
                            f"Download speed {data['download_kbps']} kbps is outside "
                            "expected VDSL2 range (100 – 300,000 kbps)"
                        )
                        assert 100 <= data["upload_kbps"] <= 300_000, (
                            f"Upload speed {data['upload_kbps']} kbps is outside "
                            "expected VDSL2 range (100 – 300,000 kbps)"
                        )
                        return
            except aiohttp.ClientError:
                continue

    pytest.skip("No DSL speed data found — skipping plausibility check")
