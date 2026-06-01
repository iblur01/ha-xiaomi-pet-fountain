"""Button platform — reset filter."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
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
    async_add_entities([FilterResetButton(coordinator, entry)])


class FilterResetButton(
    CoordinatorEntity[XiaomiPetFountainCoordinator], ButtonEntity
):
    _attr_has_entity_name = True
    _attr_translation_key = "reset_filter"
    _attr_icon = "mdi:filter-check"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self, coordinator: XiaomiPetFountainCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.data[CONF_DEVICE_ID]}_reset_filter"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_DEVICE_ID])},
            name=entry.data[CONF_DEVICE_NAME],
            manufacturer="Xiaomi",
            model="Pet Fountain",
        )

    async def async_press(self) -> None:
        await self.coordinator.async_reset_filter()
