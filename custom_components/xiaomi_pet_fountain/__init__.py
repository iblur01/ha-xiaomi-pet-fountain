"""Xiaomi Pet Fountain integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_DEVICE_ID,
    CONF_DEVICE_NAME,
    CONF_REGION,
    CONF_SESSION,
    DATA_COORDINATOR,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
)
from .coordinator import XiaomiPetFountainCoordinator
from .micloud import Session

PLATFORMS = ["switch", "sensor", "binary_sensor", "select", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = Session.from_dict(entry.data[CONF_SESSION])
    coordinator = XiaomiPetFountainCoordinator(
        hass=hass,
        session=session,
        region=entry.data[CONF_REGION],
        device_id=entry.data[CONF_DEVICE_ID],
        device_name=entry.data[CONF_DEVICE_NAME],
        poll_interval=DEFAULT_POLL_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
