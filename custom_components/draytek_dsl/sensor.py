"""DSL speed sensors for DrayTek Vigor."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfDataRate
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DraytekDslCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DraytekDslCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            DraytekDslSpeedSensor(coordinator, entry, "download"),
            DraytekDslSpeedSensor(coordinator, entry, "upload"),
        ]
    )


class DraytekDslSpeedSensor(CoordinatorEntity[DraytekDslCoordinator], SensorEntity):
    """A sensor reporting the DSL downstream or upstream sync speed in Mbit/s."""

    _attr_device_class = SensorDeviceClass.DATA_RATE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfDataRate.MEGABITS_PER_SECOND
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DraytekDslCoordinator,
        entry: ConfigEntry,
        direction: str,
    ) -> None:
        super().__init__(coordinator)
        self._direction = direction
        self._attr_unique_id = f"{entry.entry_id}_{direction}_speed"
        self._attr_name = f"DSL {direction.capitalize()} Speed"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"DrayTek Vigor ({coordinator.host})",
            manufacturer="DrayTek",
            model="Vigor 2862",
            configuration_url=f"http://{coordinator.host}",
        )

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        kbps = self.coordinator.data.get(f"{self._direction}_kbps")
        if kbps is None:
            return None
        return round(kbps / 1000, 3)
