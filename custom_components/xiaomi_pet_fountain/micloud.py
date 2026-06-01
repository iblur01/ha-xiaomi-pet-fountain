"""Xiaomi MiCloud API client — auth + MiOT cloud protocol."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Any

import aiohttp

SERVICE_LOGIN_URL = "https://account.xiaomi.com/pass/serviceLogin"
SERVICE_LOGIN_AUTH2_URL = "https://account.xiaomi.com/pass/serviceLoginAuth2"
USER_AGENT = "APP/com.xiaomi.mihome APPV/6.0.89 Channel/MI-COM-BD-00059-00 OSVersion/MIUI-12.0.1 Android/28"


@dataclass
class Session:
    user_id: str
    ssecurity: str
    service_token: str
    saved_at: str

    def as_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "ssecurity": self.ssecurity,
            "service_token": self.service_token,
            "saved_at": self.saved_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        return cls(
            user_id=data["user_id"],
            ssecurity=data["ssecurity"],
            service_token=data["service_token"],
            saved_at=data.get("saved_at", ""),
        )


@dataclass
class DeviceInfo:
    did: str
    model: str
    name: str


class MiCloudAuthError(Exception):
    pass


class MiCloud2FARequired(Exception):
    def __init__(self, notification_url: str) -> None:
        super().__init__("2FA required")
        self.notification_url = notification_url


class MiCloudAuth:
    """Handles Xiaomi account authentication."""

    def __init__(self, region: str = "de") -> None:
        self._region = region
        self._client_id = os.urandom(3).hex().upper()
        self._cookies: dict[str, str] = {
            "sdkVersion": "3.8.6",
            "deviceId": self._client_id,
        }
        self.session: Session | None = None

    async def login(self, username: str, password: str) -> None:
        """Login with username/password. Raises MiCloud2FARequired if 2FA needed."""
        pwd_hash = hashlib.md5(password.encode()).hexdigest().upper()

        async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
            self._inject_cookies(session, ["mi.com", "xiaomi.com"])

            sign_data = await self._get_sign(session)

            form = {
                "_json": "true",
                "user": username,
                "hash": pwd_hash,
                "sid": "xiaomiio",
                "callback": sign_data.get("callback") or self._sts_url(),
                "_sign": sign_data["_sign"],
                "qs": sign_data.get("qs") or "%3Fsid%3Dxiaomiio%26_json%3Dtrue",
            }

            async with session.post(
                SERVICE_LOGIN_AUTH2_URL,
                data=form,
                headers={"User-Agent": USER_AGENT},
            ) as resp:
                login_data = self._parse_mi_json(await resp.text())

            if "notificationUrl" in login_data:
                raise MiCloud2FARequired(login_data["notificationUrl"])

            service_token = await self._fetch_service_token(
                session, login_data.get("location")
            )
            if not service_token:
                raise MiCloudAuthError("Failed to retrieve serviceToken")

            self.session = Session(
                user_id=str(login_data["userId"]),
                ssecurity=str(login_data["ssecurity"]),
                service_token=service_token,
                saved_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )

    async def submit_otp(self, notification_url: str, otp_code: str) -> None:
        """Complete 2FA with OTP code."""
        base_url = notification_url.split("/fe/service")[0]

        async with aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar()) as session:
            self._inject_cookies(session, ["mi.com", "xiaomi.com"])

            list_url = notification_url.replace(
                "fe/service/identity/authStart", "identity/list"
            )
            async with session.get(
                list_url, headers={"User-Agent": USER_AGENT}
            ) as resp:
                list_data = self._parse_mi_json(await resp.text())

            flag = list_data.get("flag", 4)
            verify_endpoint = (
                "/identity/auth/verifyPhone"
                if flag == 4
                else "/identity/auth/verifyEmail"
            )

            async with session.post(
                f"{base_url}{verify_endpoint}",
                data={
                    "_flag": str(flag),
                    "ticket": otp_code,
                    "trust": "true",
                    "_json": "true",
                },
                headers={"User-Agent": USER_AGENT},
            ) as resp:
                verify_data = self._parse_mi_json(await resp.text())

            if verify_data.get("code") != 0:
                raise MiCloudAuthError("Incorrect OTP code")

            try:
                async with session.get(
                    verify_data["location"], headers={"User-Agent": USER_AGENT}
                ):
                    pass
            except Exception:
                pass

            sign_data = await self._get_sign(session)
            if not sign_data.get("location"):
                raise MiCloudAuthError("OTP verification failed — try login again")

            service_token = await self._fetch_service_token(
                session, sign_data["location"]
            )
            if not service_token:
                raise MiCloudAuthError("Failed to retrieve serviceToken after OTP")

            self.session = Session(
                user_id=str(sign_data["userId"]),
                ssecurity=str(sign_data["ssecurity"]),
                service_token=service_token,
                saved_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )

    async def _get_sign(self, session: aiohttp.ClientSession) -> dict:
        async with session.get(
            SERVICE_LOGIN_URL,
            params={"sid": "xiaomiio", "_json": "true"},
            headers={"User-Agent": USER_AGENT},
        ) as resp:
            return self._parse_mi_json(await resp.text())

    def _inject_cookies(
        self, session: aiohttp.ClientSession, domains: list[str]
    ) -> None:
        for domain in domains:
            for name, value in self._cookies.items():
                session.cookie_jar.update_cookies(
                    {name: value}, response_url=aiohttp.client.URL(f"https://{domain}")
                )

    async def _fetch_service_token(
        self, session: aiohttp.ClientSession, location: str | None
    ) -> str | None:
        if not location:
            return None
        try:
            async with session.get(
                location, headers={"User-Agent": USER_AGENT}, allow_redirects=True
            ):
                pass
        except Exception:
            pass

        sts_url = self._sts_url()
        try:
            origin = aiohttp.client.URL(location).origin()
        except Exception:
            origin = aiohttp.client.URL(sts_url.replace("/sts", "")).origin()

        cookies = session.cookie_jar.filter_cookies(origin)
        token = cookies.get("serviceToken")
        return token.value if token else None

    def _sts_url(self) -> str:
        if self._region == "cn":
            return "https://sts.api.io.mi.com/sts"
        return f"https://{self._region}.sts.api.io.mi.com/sts"

    @staticmethod
    def _parse_mi_json(raw: str) -> dict:
        text = raw.removeprefix("&&&START&&&").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}


class MiCloudClient:
    """MiOT cloud API client for signed requests."""

    def __init__(self, session: Session, region: str = "de") -> None:
        self._session = session
        self._region = region

    def _base_url(self) -> str:
        if self._region == "cn":
            return "https://api.io.mi.com/app"
        return f"https://{self._region}.api.io.mi.com/app"

    def _generate_nonce(self) -> str:
        rand = os.urandom(8)
        ts = int(time.time() / 60).to_bytes(4, "big")
        return base64.b64encode(rand + ts).decode()

    def _sign_nonce(self, nonce: str) -> str:
        key = base64.b64decode(self._session.ssecurity)
        nonce_bytes = base64.b64decode(nonce)
        digest = hashlib.sha256(key + nonce_bytes).digest()
        return base64.b64encode(digest).decode()

    def _rc4_encrypt(self, key_b64: str, data: str) -> str:
        """RC4-drop[1024] encryption used by MiCloud protocol."""
        key = base64.b64decode(key_b64)
        s = list(range(256))
        j = 0
        for i in range(256):
            j = (j + s[i] + key[i % len(key)]) % 256
            s[i], s[j] = s[j], s[i]

        i = j = 0
        # Drop first 1024 keystream bytes
        for _ in range(1024):
            i = (i + 1) % 256
            j = (j + s[i]) % 256
            s[i], s[j] = s[j], s[i]

        buf = data.encode()
        out = []
        for byte in buf:
            i = (i + 1) % 256
            j = (j + s[i]) % 256
            s[i], s[j] = s[j], s[i]
            out.append(byte ^ s[(s[i] + s[j]) % 256])

        return base64.b64encode(bytes(out)).decode()

    def _build_request(self, path: str, params: Any) -> dict:
        nonce = self._generate_nonce()
        signed_nonce = self._sign_nonce(nonce)
        encrypted_data = self._rc4_encrypt(signed_nonce, json.dumps(params))

        msg = "\n".join([path, signed_nonce, nonce, f"data={encrypted_data}"])
        signature = base64.b64encode(
            hmac.new(
                base64.b64decode(signed_nonce), msg.encode(), hashlib.sha256
            ).digest()
        ).decode()

        return {
            "signature": signature,
            "nonce": nonce,
            "data": encrypted_data,
        }

    async def _request(self, path: str, params: Any) -> Any:
        url = f"{self._base_url()}{path}"
        body = self._build_request(path, params)

        headers = {
            "User-Agent": USER_AGENT,
            "x-xiaomi-protocal-flag-cli": "PROTOCAL-HTTP2",
            "content-type": "application/x-www-form-urlencoded",
            "Cookie": (
                f"userId={self._session.user_id}; "
                f"serviceToken={self._session.service_token}; "
                f"yetAnotherServiceToken={self._session.service_token}; "
                "locale=en_GB; timezone=GMT+02:00; is_daylight=1; "
                "dst_offset=3600000; channel=MI_APP_STORE"
            ),
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=body, headers=headers) as resp:
                resp.raise_for_status()
                result = await resp.json(content_type=None)

        if result.get("code") != 0:
            raise MiCloudAuthError(
                f"MiCloud error {result.get('code')}: {result.get('message')}"
            )
        return result.get("result")

    async def get_devices(self) -> list[DeviceInfo]:
        result = await self._request(
            "/v2/home/device_list",
            {"getVirtualModel": False, "getHuamiDevices": 0},
        )
        devices = []
        for item in (result or {}).get("list", []):
            devices.append(
                DeviceInfo(
                    did=str(item["did"]),
                    model=item.get("model", ""),
                    name=item.get("name", item.get("did", "")),
                )
            )
        return devices

    async def miot_get(self, did: str, props: list[tuple[int, int]]) -> list[Any]:
        """Get MiOT properties. props = list of (siid, piid)."""
        params = [{"did": did, "siid": siid, "piid": piid} for siid, piid in props]
        result = await self._request(
            f"/v2/home/rpc/{did}",
            {"method": "get_properties", "params": params},
        )
        return [item.get("value") for item in (result or [])]

    async def miot_set(self, did: str, siid: int, piid: int, value: Any) -> None:
        """Set a single MiOT property."""
        await self._request(
            f"/v2/home/rpc/{did}",
            {
                "method": "set_properties",
                "params": [{"did": did, "siid": siid, "piid": piid, "value": value}],
            },
        )

    async def miot_action(
        self, did: str, siid: int, aiid: int, in_params: list | None = None
    ) -> None:
        """Invoke a MiOT action."""
        await self._request(
            f"/v2/home/rpc/{did}",
            {
                "method": "action",
                "params": {
                    "did": did,
                    "siid": siid,
                    "aiid": aiid,
                    "in": in_params or [],
                },
            },
        )
