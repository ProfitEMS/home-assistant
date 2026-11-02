"""Config flow for the ProfitEMS integration."""

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import InvalidAuth, ProfitEmsClient, ProfitEmsError, RateLimited
from .const import DOMAIN

_SCHEMA = vol.Schema({vol.Required(CONF_API_KEY): str})


class ProfitEmsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle setup and re-authentication with an access key from the ProfitEMS app."""

    VERSION = 1

    async def _async_validate(
        self, user_input: dict[str, Any], errors: dict[str, str]
    ) -> tuple[str, dict[str, Any]] | None:
        """Return the cleaned key and installation data, or fill in errors."""
        api_key = user_input[CONF_API_KEY].strip()
        client = ProfitEmsClient(async_get_clientsession(self.hass), api_key)
        try:
            return api_key, await client.async_get_installation()
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except RateLimited:
            errors["base"] = "rate_limited"
        except ProfitEmsError:
            errors["base"] = "cannot_connect"
        return None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the access key."""
        errors: dict[str, str] = {}
        if user_input is not None and (
            result := await self._async_validate(user_input, errors)
        ):
            api_key, data = result
            serial = data["numerBramki"]
            await self.async_set_unique_id(serial)
            self._abort_if_unique_id_configured(updates={CONF_API_KEY: api_key})
            return self.async_create_entry(
                title=f"ProfitEMS {serial}", data={CONF_API_KEY: api_key}
            )
        return self.async_show_form(step_id="user", data_schema=_SCHEMA, errors=errors)

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Start re-authentication after the key stopped working."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for a new access key for the same installation."""
        errors: dict[str, str] = {}
        if user_input is not None and (
            result := await self._async_validate(user_input, errors)
        ):
            api_key, data = result
            await self.async_set_unique_id(data["numerBramki"])
            self._abort_if_unique_id_mismatch()
            return self.async_update_reload_and_abort(
                self._get_reauth_entry(), data_updates={CONF_API_KEY: api_key}
            )
        return self.async_show_form(
            step_id="reauth_confirm", data_schema=_SCHEMA, errors=errors
        )
