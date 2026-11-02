"""Data update coordinator for the ProfitEMS integration."""

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import InvalidAuth, ProfitEmsClient, ProfitEmsError, RateLimited
from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

type ProfitEmsConfigEntry = ConfigEntry[ProfitEmsCoordinator]


class ProfitEmsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls the ProfitEMS API."""

    config_entry: ProfitEmsConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ProfitEmsConfigEntry,
        client: ProfitEmsClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.async_get_installation()
        except InvalidAuth as err:
            raise ConfigEntryAuthFailed("The access key is no longer valid") from err
        except RateLimited as err:
            raise UpdateFailed("Request limit exceeded", retry_after=err.retry_after) from err
        except ProfitEmsError as err:
            raise UpdateFailed(f"Could not read installation data: {err}") from err
