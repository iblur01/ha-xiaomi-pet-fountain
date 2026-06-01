"""Binary sensor platform — water shortage, pump blocked, filter expired, lid removed."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_ID, CONF_DEVICE_NAME, DATA_COORDINATOR, DOMAIN
from .coordinator import FountainData, XiaomiPetFountainCoordinator


@dataclass(frozen=True, kw_only=True)
class FountainBinarySensorDescription(BinarySensorEntityDescription):
    value_fn: Callable[[FountainData], bool]


BINARY_SENSORS: tuple[FountainBinarySensorDescription, ...] = (
    FountainBinarySensorDescription(
        key="water_shortage",
        translation_key="water_shortage",
        device_class=BinarySensorDeviceClass.MOISTURE,
        value_fn=lambda d: d.water_shortage,
    ),
    FountainBinarySensorDescription(
        key="pump_blocked",
        translation_key="pump_blocked",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.pump_blocked,
    ),
    FountainBinarySensorDescription(
        key="filter_expired",
        translation_key="filter_expired",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:filter-off",
        value_fn=lambda d: d.filter_expired,
    ),
    FountainBinarySensorDescription(
        key="lid_removed",
        translation_key="lid_removed",
        device_class=BinarySensorDeviceClass.OPENING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.lid_removed,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: XiaomiPetFountainCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities(
        FountainBinarySensor(coordinator, entry, desc) for desc in BINARY_SENSORS
    )


class FountainBinarySensor(
    CoordinatorEntity[XiaomiPetFountainCoordinator], BinarySensorEntity
):
    _attr_has_entity_name = True
    entity_description: FountainBinarySensorDescription

    def __init__(
        self,
        coordinator: XiaomiPetFountainCoordinator,
        entry: ConfigEntry,
        description: FountainBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.data[CONF_DEVICE_ID]}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_DEVICE_ID])},
            name=entry.data[CONF_DEVICE_NAME],
            manufacturer="Xiaomi",
            model="Pet Fountain",
        )

    @property
    def is_on(self) -> bool:
        return self.entity_description.value_fn(self.coordinator.data)
