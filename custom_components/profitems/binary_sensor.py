"""Binary sensors of the ProfitEMS integration: ready-made signals for automations."""

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ProfitEmsConfigEntry
from .entity import ProfitEmsEntity


@dataclass(frozen=True, kw_only=True)
class ProfitEmsBinaryDescription(BinarySensorEntityDescription):
    """Describes where a binary sensor reads its value."""

    section: str
    field: str


BINARY_SENSORS = (
    ProfitEmsBinaryDescription(
        key="pv_surplus_active",
        translation_key="pv_surplus_active",
        section="sygnaly",
        field="nadwyzkaPv",
    ),
    ProfitEmsBinaryDescription(
        key="battery_full",
        translation_key="battery_full",
        section="sygnaly",
        field="bateriaPelna",
    ),
    ProfitEmsBinaryDescription(
        key="cheapest_hour_now",
        translation_key="cheapest_hour_now",
        section="sygnaly",
        field="najtanszaGodzinaDnia",
    ),
    ProfitEmsBinaryDescription(
        key="control_active",
        translation_key="control_active",
        entity_category=EntityCategory.DIAGNOSTIC,
        section="system",
        field="sterowanieAktywne",
    ),
    ProfitEmsBinaryDescription(
        key="island_mode",
        translation_key="island_mode",
        section="polaczenie",
        field="pracaWyspowa",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ProfitEmsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up binary sensors."""
    async_add_entities(
        ProfitEmsBinarySensor(entry.runtime_data, description)
        for description in BINARY_SENSORS
    )


class ProfitEmsBinarySensor(ProfitEmsEntity, BinarySensorEntity):
    """A yes/no value read from the installation data."""

    entity_description: ProfitEmsBinaryDescription

    @property
    def is_on(self) -> bool | None:
        """Return the state; None means the server has no data for it."""
        description = self.entity_description
        return self.coordinator.data[description.section].get(description.field)
