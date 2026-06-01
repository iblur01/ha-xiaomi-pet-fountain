"""Sensor platform — battery, filter life, filter days, fault."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_ID, CONF_DEVICE_NAME, DATA_COORDINATOR, DOMAIN
from .coordinator import FountainData, XiaomiPetFountainCoordinator


@dataclass(frozen=True, kw_only=True)
class FountainSensorDescription(SensorEntityDescription):
    value_fn: Callable[[FountainData], int | str | None]


SENSORS: tuple[FountainSensorDescription, ...] = (
    FountainSensorDescription(
        key="battery",
        translation_key="battery",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.battery_level,
    ),
    FountainSensorDescription(
        key="filter_life",
        translation_key="filter_life",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:filter",
        value_fn=lambda d: d.filter_life_left,
    ),
    FountainSensorDescription(
        key="filter_days",
        translation_key="filter_days",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.DAYS,
        icon="mdi:filter-clock",
        value_fn=lambda d: d.filter_left_days,
    ),
    FountainSensorDescription(
        key="fault",
        translation_key="fault",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:alert-circle-outline",
        options=["none", "water_shortage", "pump_blocked", "filter_expired", "lid_removed"],
        value_fn=lambda d: d.fault_label,
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
        FountainSensor(coordinator, entry, desc) for desc in SENSORS
    )


class FountainSensor(
    CoordinatorEntity[XiaomiPetFountainCoordinator], SensorEntity
):
    _attr_has_entity_name = True
    entity_description: FountainSensorDescription

    def __init__(
        self,
        coordinator: XiaomiPetFountainCoordinator,
        entry: ConfigEntry,
        description: FountainSensorDescription,
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
    def native_value(self) -> int | str | None:
        return self.entity_description.value_fn(self.coordinator.data)
