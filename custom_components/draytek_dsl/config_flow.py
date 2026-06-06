"""Config flow for DrayTek DSL Speed Monitor."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import DOMAIN, DEFAULT_PORT
from .coordinator import DraytekDslCoordinator

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.All(
            int, vol.Range(min=1, max=65535)
        ),
        vol.Required(CONF_USERNAME, default="admin"): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def _validate_credentials(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Attempt a full data fetch to validate the provided credentials and host."""
    coordinator = DraytekDslCoordinator(
        hass=hass,
        host=data[CONF_HOST],
        port=data.get(CONF_PORT, DEFAULT_PORT),
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
    )
    await coordinator.async_refresh()


class DraytekDslConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the initial setup flow for the DrayTek DSL integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            unique_id = f"{user_input[CONF_HOST]}:{user_input.get(CONF_PORT, DEFAULT_PORT)}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            try:
                await _validate_credentials(self.hass, user_input)
            except UpdateFailed:
                errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error validating DrayTek connection")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"DrayTek Vigor ({user_input[CONF_HOST]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
