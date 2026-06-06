"""DrayTek DSL coordinator: authenticates, scrapes DSL status, parses speeds."""
from __future__ import annotations

import base64
import logging
import re
from datetime import timedelta
from urllib.parse import quote_plus

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, DSL_STATUS_PATHS

_LOGGER = logging.getLogger(__name__)

# Regex patterns for downstream speed (tries with and without Kbps unit suffix)
_DS_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"Down\s*Speed[^<\d]*?(\d+)\s*[Kk]bps", re.IGNORECASE),
    re.compile(r"Down(?:stream)?\s*(?:Actual\s*)?Rate[^<\d]*?(\d+)\s*[Kk]bps", re.IGNORECASE),
    re.compile(r"\bDS\s*(?:Actual\s*)?Rate[^<\d]*?(\d+)\s*[Kk]bps", re.IGNORECASE),
    re.compile(r"Downstream[^<\d]*?(\d+)\s*[Kk]bps", re.IGNORECASE),
    re.compile(r"Down\s*Speed[^<\d]*?(\d+)", re.IGNORECASE),
    re.compile(r"Down(?:stream)?\s*(?:Actual\s*)?Rate[^<\d]*?(\d+)", re.IGNORECASE),
]

# Regex patterns for upstream speed
_US_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"Up\s*Speed[^<\d]*?(\d+)\s*[Kk]bps", re.IGNORECASE),
    re.compile(r"Up(?:stream)?\s*(?:Actual\s*)?Rate[^<\d]*?(\d+)\s*[Kk]bps", re.IGNORECASE),
    re.compile(r"\bUS\s*(?:Actual\s*)?Rate[^<\d]*?(\d+)\s*[Kk]bps", re.IGNORECASE),
    re.compile(r"Upstream[^<\d]*?(\d+)\s*[Kk]bps", re.IGNORECASE),
    re.compile(r"Up\s*Speed[^<\d]*?(\d+)", re.IGNORECASE),
    re.compile(r"Up(?:stream)?\s*(?:Actual\s*)?Rate[^<\d]*?(\d+)", re.IGNORECASE),
]


def _encode_credential(value: str) -> str:
    """Base64-encode then URL-encode a credential, as expected by wlogin.cgi."""
    return quote_plus(base64.b64encode(value.encode()).decode())


def _parse_speeds(html: str) -> dict[str, int | None]:
    """Extract downstream and upstream kbps values from the DSL status page HTML."""
    download_kbps: int | None = None
    upload_kbps: int | None = None

    for pattern in _DS_PATTERNS:
        match = pattern.search(html)
        if match:
            download_kbps = int(match.group(1))
            _LOGGER.debug("Parsed downstream speed: %d kbps", download_kbps)
            break

    for pattern in _US_PATTERNS:
        match = pattern.search(html)
        if match:
            upload_kbps = int(match.group(1))
            _LOGGER.debug("Parsed upstream speed: %d kbps", upload_kbps)
            break

    return {"download_kbps": download_kbps, "upload_kbps": upload_kbps}


class DraytekDslCoordinator(DataUpdateCoordinator[dict[str, int | None]]):
    """Polls the DrayTek router for DSL line speeds every minute."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        username: str,
        password: str,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.host = host
        self._port = port
        self._username = username
        self._password = password
        # Use HTTPS automatically when port 443 is specified
        scheme = "https" if port == 443 else "http"
        self._base_url = f"{scheme}://{host}:{port}"

    async def _async_update_data(self) -> dict[str, int | None]:
        timeout = aiohttp.ClientTimeout(total=15)
        # ssl=False skips certificate verification for HTTPS (routers use self-signed certs)
        connector = aiohttp.TCPConnector(ssl=False)
        try:
            async with aiohttp.ClientSession(
                connector=connector, timeout=timeout
            ) as session:
                await self._login(session)
                return await self._fetch_dsl_status(session)
        except aiohttp.ClientConnectorError as err:
            raise UpdateFailed(
                f"Cannot connect to router at {self._base_url}: {err}"
            ) from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Router communication error: {err}") from err

    async def _login(self, session: aiohttp.ClientSession) -> None:
        """Authenticate with the router web interface via wlogin.cgi."""
        url = (
            f"{self._base_url}/cgi-bin/wlogin.cgi"
            f"?aa={_encode_credential(self._username)}"
            f"&ab={_encode_credential(self._password)}"
        )
        async with session.get(url) as resp:
            # DrayTek may redirect (302) on successful login
            if resp.status not in (200, 302):
                raise UpdateFailed(
                    f"Router login failed with HTTP {resp.status}. "
                    "Check your username and password."
                )

    async def _fetch_dsl_status(
        self, session: aiohttp.ClientSession
    ) -> dict[str, int | None]:
        """Try each candidate DSL status page path until one returns speed data."""
        for path in DSL_STATUS_PATHS:
            url = f"{self._base_url}{path}"
            try:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        _LOGGER.debug("Path %s returned HTTP %d, skipping", path, resp.status)
                        continue
                    html = await resp.text()
                    data = _parse_speeds(html)
                    if data["download_kbps"] is not None or data["upload_kbps"] is not None:
                        _LOGGER.debug("Retrieved DSL status from %s", url)
                        return data
                    _LOGGER.debug("No speed data found at %s", path)
            except aiohttp.ClientError as err:
                _LOGGER.debug("Error fetching %s: %s", url, err)

        raise UpdateFailed(
            f"Could not find DSL speed data on {self._base_url}. "
            "The router may still be syncing, or the status page path differs for "
            "your firmware version. Enable debug logging for details."
        )
