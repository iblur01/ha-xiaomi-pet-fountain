"""Config flow for Xiaomi Pet Fountain."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME

from .const import (
    CONF_DEVICE_ID,
    CONF_DEVICE_NAME,
    CONF_PASSWORD,
    CONF_REGION,
    CONF_SESSION,
    CONF_USERNAME,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_REGION,
    DOMAIN,
    MODEL_PATTERNS,
    REGIONS,
)
from .micloud import (
    MiCloud2FARequired,
    MiCloudAuth,
    MiCloudAuthError,
    Session,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_REGION, default=DEFAULT_REGION): vol.In(REGIONS),
    }
)

STEP_OTP_SCHEMA = vol.Schema(
    {
        vol.Required("otp_code"): str,
    }
)


class XiaomiPetFountainConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._auth: MiCloudAuth | None = None
        self._notification_url: str | None = None
        self._session: Session | None = None
        self._region: str = DEFAULT_REGION
        self._fountains: list[dict] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            self._region = user_input.get(CONF_REGION, DEFAULT_REGION)

            self._auth = MiCloudAuth(region=self._region)
            try:
                await self._auth.login(username, password)
                self._session = self._auth.session
                return await self._async_discover_fountains()

            except MiCloud2FARequired as exc:
                self._notification_url = exc.notification_url
                return await self.async_step_otp()

            except MiCloudAuthError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected error during login")
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )

    async def async_step_otp(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None and self._auth and self._notification_url:
            try:
                await self._auth.submit_otp(
                    self._notification_url, user_input["otp_code"]
                )
                self._session = self._auth.session
                return await self._async_discover_fountains()
            except MiCloudAuthError:
                errors["base"] = "invalid_otp"
            except Exception:
                _LOGGER.exception("Unexpected error during OTP")
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="otp",
            data_schema=STEP_OTP_SCHEMA,
            errors=errors,
        )

    async def _async_discover_fountains(self) -> ConfigFlowResult:
        assert self._session is not None
        from .micloud import MiCloudClient

        client = MiCloudClient(self._session, self._region)
        try:
            devices = await client.get_devices()
        except Exception:
            _LOGGER.exception("Failed to list devices")
            return self.async_abort(reason="cannot_connect")

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
