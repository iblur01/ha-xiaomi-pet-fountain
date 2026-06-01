"""DataUpdateCoordinator for Xiaomi Pet Fountain."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ACTION_RESET_FILTER,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    FAULT_LABELS,
    MODE_LABELS,
    MODE_VALUES,
    PROP_BATTERY,
    PROP_FAULT,
    PROP_FILTER_LEFT_TIME,
    PROP_FILTER_LIFE_LEFT,
    PROP_MODE,
    PROP_ON,
    PROP_WATER_SHORTAGE,
)
from .micloud import MiCloudClient, Session

_LOGGER = logging.getLogger(__name__)

ALL_PROPS = [
    PROP_ON,
    PROP_FAULT,
    PROP_MODE,
    PROP_WATER_SHORTAGE,
    PROP_FILTER_LIFE_LEFT,
    PROP_FILTER_LEFT_TIME,
    PROP_BATTERY,
]


@dataclass
class FountainData:
    on: bool
    fault_code: int
    fault_label: str
    mode_code: int
    mode_label: str
    water_shortage: bool
    filter_life_left: int
    filter_left_days: int
    battery_level: int

    @property
    def pump_blocked(self) -> bool:
        return self.fault_code == 2

    @property
    def filter_expired(self) -> bool:
        return self.fault_code == 3

    @property
    def lid_removed(self) -> bool:
        return self.fault_code == 4


class XiaomiPetFountainCoordinator(DataUpdateCoordinator[FountainData]):
    def __init__(
        self,
        hass: HomeAssistant,
        session: Session,
        region: str,
        device_id: str,
        device_name: str,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
    ) -> None:
        self._client = MiCloudClient(session, region)
        self.device_id = device_id
        self.device_name = device_name

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{device_id}",
            update_interval=timedelta(seconds=poll_interval),
        )

    async def _async_update_data(self) -> FountainData:
        try:
            values = await self._client.miot_get(self.device_id, ALL_PROPS)
        except Exception as err:
            raise UpdateFailed(f"MiCloud poll failed: {err}") from err

        (on, fault, mode, water_shortage, filter_life, filter_days, battery) = values

        fault_int = int(fault or 0)
        mode_int = int(mode or 0)

        return FountainData(
            on=bool(on),
            fault_code=fault_int,
            fault_label=FAULT_LABELS.get(fault_int, "unknown"),
            mode_code=mode_int,
            mode_label=MODE_LABELS.get(mode_int, "sensor"),
            water_shortage=bool(water_shortage),
            filter_life_left=int(filter_life or 0),
            filter_left_days=int(filter_days or 0),
            battery_level=int(battery or 0),
        )

    async def async_set_on(self, on: bool) -> None:
        siid, piid = PROP_ON
        await self._client.miot_set(self.device_id, siid, piid, on)
        await self.async_request_refresh()

    async def async_set_mode(self, mode_label: str) -> None:
        mode_code = MODE_VALUES.get(mode_label, 0)
        siid, piid = PROP_MODE
        await self._client.miot_set(self.device_id, siid, piid, mode_code)
        await self.async_request_refresh()

    async def async_reset_filter(self) -> None:
        siid, aiid = ACTION_RESET_FILTER
        await self._client.miot_action(self.device_id, siid, aiid)
        await self.async_request_refresh()
