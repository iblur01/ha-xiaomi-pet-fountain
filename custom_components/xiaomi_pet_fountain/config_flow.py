"""Config flow for Xiaomi Pet Fountain."""
from __future__ import annotations

import logging
import time
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import (
    CONF_DEVICE_ID,
    CONF_DEVICE_NAME,
    CONF_REGION,
    CONF_SERVICE_TOKEN,
    CONF_SESSION,
    CONF_SSECURITY,
    CONF_USER_ID,
    DEFAULT_REGION,
    DOMAIN,
    MODEL_PATTERNS,
    REGIONS,
)
from .micloud import MiCloudClient, Session

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USER_ID): str,
        vol.Required(CONF_SSECURITY): str,
        vol.Required(CONF_SERVICE_TOKEN): str,
        vol.Optional(CONF_REGION, default=DEFAULT_REGION): vol.In(REGIONS),
    }
)


class XiaomiPetFountainConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._session: Session | None = None
        self._region: str = DEFAULT_REGION
        self._fountains: list[dict] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            self._region = user_input.get(CONF_REGION, DEFAULT_REGION)
            self._session = Session(
                user_id=str(user_input[CONF_USER_ID]).strip(),
                ssecurity=str(user_input[CONF_SSECURITY]).strip(),
                service_token=str(user_input[CONF_SERVICE_TOKEN]).strip(),
                saved_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )
            return await self._async_discover_fountains(errors)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )

    async def _async_discover_fountains(
        self, errors: dict[str, str]
    ) -> ConfigFlowResult:
        assert self._session is not None

        client = MiCloudClient(self._session, self._region)
        try:
            devices = await client.get_devices()
        except Exception:
            _LOGGER.exception("Failed to list devices")
            errors["base"] = "invalid_auth"
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_SCHEMA,
                errors=errors,
            )

        self._fountains = [
            {"did": d.did, "name": d.name, "model": d.model}
            for d in devices
            if any(p in d.model for p in MODEL_PATTERNS)
        ]

        if not self._fountains:
            return self.async_abort(reason="no_devices_found")

        if len(self._fountains) == 1:
            return self._async_create_entry(self._fountains[0])

        return await self.async_step_pick_device()

    async def async_step_pick_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            did = user_input[CONF_DEVICE_ID]
            device = next(f for f in self._fountains if f["did"] == did)
            return self._async_create_entry(device)

        options = {f["did"]: f"{f['name']} ({f['model']})" for f in self._fountains}

        return self.async_show_form(
            step_id="pick_device",
            data_schema=vol.Schema(
                {vol.Required(CONF_DEVICE_ID): vol.In(options)}
            ),
        )

    def _async_create_entry(self, device: dict) -> ConfigFlowResult:
        assert self._session is not None
        return self.async_create_entry(
            title=device["name"],
            data={
                CONF_DEVICE_ID: device["did"],
                CONF_DEVICE_NAME: device["name"],
                CONF_REGION: self._region,
                CONF_SESSION: self._session.as_dict(),
            },
        )
