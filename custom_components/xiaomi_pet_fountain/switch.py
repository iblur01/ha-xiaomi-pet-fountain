"""Switch platform — pump on/off."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_ID, CONF_DEVICE_NAME, DATA_COORDINATOR, DOMAIN
from .coordinator import XiaomiPetFountainCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: XiaomiPetFountainCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities([FountainPumpSwitch(coordinator, entry)])


class FountainPumpSwitch(CoordinatorEntity[XiaomiPetFountainCoordinator], SwitchEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "pump"

    def __init__(
        self, coordinator: XiaomiPetFountainCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.data[CONF_DEVICE_ID]}_pump"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_DEVICE_ID])},
            name=entry.data[CONF_DEVICE_NAME],
            manufacturer="Xiaomi",
            model="Pet Fountain",
        )

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.on

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_on(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_on(False)
