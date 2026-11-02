"""Sensors of the ProfitEMS integration."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import ProfitEmsConfigEntry
from .entity import ProfitEmsEntity

type Data = dict[str, Any]


def _timestamp(value: str | None) -> datetime | None:
    return dt_util.parse_datetime(value) if value else None


@dataclass(frozen=True, kw_only=True)
class ProfitEmsSensorDescription(SensorEntityDescription):
    """Describes a sensor and where its value comes from."""

    value_fn: Callable[[Data], Any]
    attributes_fn: Callable[[Data], dict[str, Any]] | None = None


def _power(key: str, field: str, section: str = "teraz") -> ProfitEmsSensorDescription:
    return ProfitEmsSensorDescription(
        key=key,
        translation_key=key,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda data: data[section].get(field),
    )


SENSORS = (
    ProfitEmsSensorDescription(
        key="battery_level",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data["teraz"].get("socPct"),
    ),
    _power("pv_power", "pvW"),
    _power("home_power", "domW"),
    _power("grid_power", "siecW"),
    _power("battery_power", "bateriaW"),
    _power("pv_surplus", "nadwyzkaPvW", "sygnaly"),
    # A plain text sensor, not an enum: API version 1 may add new modes without breaking the entity.
    ProfitEmsSensorDescription(
        key="mode",
        translation_key="mode",
        value_fn=lambda data: data["system"].get("tryb"),
        attributes_fn=lambda data: {
            "since": data["system"].get("trybOd"),
            "plan": data.get("plan", []),
        },
    ),
    ProfitEmsSensorDescription(
        key="rce_price",
        translation_key="rce_price",
        native_unit_of_measurement="PLN/kWh",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=4,
        value_fn=lambda data: data["ceny"].get("teraz"),
        attributes_fn=lambda data: {
            "today": data["ceny"].get("dzis"),
            "tomorrow": data["ceny"].get("jutro"),
        },
    ),
    ProfitEmsSensorDescription(
        key="cheapest_hour",
        translation_key="cheapest_hour",
        value_fn=lambda data: data["sygnaly"].get("najtanszaGodzina"),
    ),
    ProfitEmsSensorDescription(
        key="connection",
        translation_key="connection",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data["polaczenie"].get("stan"),
    ),
    ProfitEmsSensorDescription(
        key="last_reading",
        translation_key="last_reading",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _timestamp(data["polaczenie"].get("ostatniOdczyt")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ProfitEmsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up sensors."""
    async_add_entities(
        ProfitEmsSensor(entry.runtime_data, description) for description in SENSORS
    )


class ProfitEmsSensor(ProfitEmsEntity, SensorEntity):
    """A value read from the installation data."""

    entity_description: ProfitEmsSensorDescription

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional data, such as the plan or hourly prices."""
        if (attributes_fn := self.entity_description.attributes_fn) is None:
            return None
        return attributes_fn(self.coordinator.data)
