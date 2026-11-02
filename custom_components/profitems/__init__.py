"""The ProfitEMS integration: read-only installation data for Home Assistant."""

from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ProfitEmsClient
from .coordinator import ProfitEmsConfigEntry, ProfitEmsCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ProfitEmsConfigEntry) -> bool:
    """Set up ProfitEMS from a config entry."""
    client = ProfitEmsClient(async_get_clientsession(hass), entry.data[CONF_API_KEY])
    coordinator = ProfitEmsCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ProfitEmsConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
