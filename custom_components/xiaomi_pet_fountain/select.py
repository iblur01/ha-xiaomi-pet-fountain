"""Select platform — fountain flow mode."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_ID, CONF_DEVICE_NAME, DATA_COORDINATOR, DOMAIN, MODE_LABELS
from .coordinator import XiaomiPetFountainCoordinator

MODE_OPTIONS = list(MODE_LABELS.values())


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: XiaomiPetFountainCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities([FountainModeSelect(coordinator, entry)])


class FountainModeSelect(
    CoordinatorEntity[XiaomiPetFountainCoordinator], SelectEntity
):
    _attr_has_entity_name = True
    _attr_translation_key = "mode"
    _attr_options = MODE_OPTIONS
    _attr_icon = "mdi:water-pump"

    def __init__(
        self, coordinator: XiaomiPetFountainCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.data[CONF_DEVICE_ID]}_mode"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_DEVICE_ID])},
            name=entry.data[CONF_DEVICE_NAME],
            manufacturer="Xiaomi",
            model="Pet Fountain",
        )

    @property
    def current_option(self) -> str:
        return self.coordinator.data.mode_label

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_mode(option)
