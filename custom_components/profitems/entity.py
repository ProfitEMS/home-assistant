"""Base entity for the ProfitEMS integration."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ProfitEmsCoordinator


class ProfitEmsEntity(CoordinatorEntity[ProfitEmsCoordinator]):
    """An entity of one EMS Connect gateway."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: ProfitEmsCoordinator, description: EntityDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        serial = coordinator.data["numerBramki"]
        self._attr_unique_id = f"{serial}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            manufacturer="ProfitEMS",
            model="EMS Connect",
            name=f"ProfitEMS {serial}",
            serial_number=serial,
            configuration_url="https://panel.profitems.pl",
        )
