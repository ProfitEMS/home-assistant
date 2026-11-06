"""Sensors of the ProfitEMS integration."""

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfEnergy, UnitOfPower
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
    # The value starts again from zero at local midnight (state_class TOTAL needs last_reset).
    resets_daily: bool = False


def _power(key: str, field: str, section: str = "teraz") -> ProfitEmsSensorDescription:
    return ProfitEmsSensorDescription(
        key=key,
        translation_key=key,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda data: data[section].get(field),
    )


def _energy(key: str, field: str) -> ProfitEmsSensorDescription:
    # Inverter counters reset at the inverter's midnight; TOTAL_INCREASING handles the reset in the Energy panel.
    # Older API responses have no "energiaDzis", so the sensor stays unknown instead of failing.
    return ProfitEmsSensorDescription(
        key=key,
        translation_key=key,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=1,
        value_fn=lambda data: (data.get("energiaDzis") or {}).get(field),
    )


ENERGY_FIELDS = {
    "pv_energy_today": "pvKwh",
    "home_energy_today": "domKwh",
    "grid_import_today": "poborKwh",
    "grid_export_today": "oddawanieKwh",
    "battery_charge_today": "ladowanieKwh",
    "battery_discharge_today": "rozladowanieKwh",
}


def _value_attributes(data: Data) -> dict[str, Any]:
    value = data.get("wartoscDzis") or {}
    return {
        "from_panels": value.get("zPaneliZl"),
        "from_system": value.get("zSystemuZl"),
        "export_revenue": value.get("sprzedazZl"),
        "data_coverage": value.get("pokrycieDanychPct"),
        "calculated_at": value.get("przeliczono"),
    }


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
            "plan_today": data.get("planDoby", []),
            "plan_tomorrow": data.get("planJutro"),
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
            "prices_today": data["ceny"].get("godzinyDzis"),
            "prices_tomorrow": data["ceny"].get("godzinyJutro"),
        },
    ),
    *(_energy(key, field) for key, field in ENERGY_FIELDS.items()),
    ProfitEmsSensorDescription(
        key="value_today",
        translation_key="value_today",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        resets_daily=True,
        native_unit_of_measurement="PLN",
        suggested_display_precision=2,
        value_fn=lambda data: (data.get("wartoscDzis") or {}).get("razemZl"),
        attributes_fn=_value_attributes,
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
    # Many inverter brands do not report some daily counters. Such energy sensors are created disabled,
    # so they do not clutter the device; the user can still enable them.
    energy = (entry.runtime_data.data or {}).get("energiaDzis") or {}
    descriptions = [
        replace(description, entity_registry_enabled_default=False)
        if description.key in ENERGY_FIELDS and energy.get(ENERGY_FIELDS[description.key]) is None
        else description
        for description in SENSORS
    ]
    async_add_entities(ProfitEmsSensor(entry.runtime_data, description) for description in descriptions)


class ProfitEmsSensor(ProfitEmsEntity, SensorEntity):
    """A value read from the installation data."""

    entity_description: ProfitEmsSensorDescription
    # The plan starts at the current minute and the hourly prices are long lists: recording them would add
    # a new attributes row every minute. They stay available to automations, only the database skips them.
    _unrecorded_attributes = frozenset(
        {"plan", "plan_today", "plan_tomorrow", "today", "tomorrow", "prices_today", "prices_tomorrow"}
    )

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def last_reset(self) -> datetime | None:
        """Return local midnight for values that start again every day."""
        return dt_util.start_of_local_day() if self.entity_description.resets_daily else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional data, such as the plan or hourly prices."""
        if (attributes_fn := self.entity_description.attributes_fn) is None:
            return None
        return attributes_fn(self.coordinator.data)
