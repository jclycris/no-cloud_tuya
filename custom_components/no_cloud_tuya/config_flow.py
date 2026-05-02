"""Config Flow No-Cloud Tuya — avec authentification par QR Code."""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    DOMAIN,
    CONF_HOST, CONF_DEVICE_ID, CONF_LOCAL_KEY, CONF_PROTOCOL_VERSION,
    CONF_SCAN_INTERVAL, CONF_NAME,
    CONF_REGION, CONF_CLIENT_ID, CONF_CLIENT_SECRET,
    DEFAULT_PROTOCOL_VERSION, DEFAULT_SCAN_INTERVAL,
    PROTOCOL_VERSIONS, TUYA_REGIONS,
)
from .tuya_cloud_auth import TuyaCloudAuth
from .tuya_device import NoCLoudTuyaDevice

_LOGGER = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  ÉTAPES :
#  1. auth       → Client ID + Secret + Région
#  2. qr_code    → Affiche le QR à scanner
#  3. qr_wait    → Poll jusqu'au scan (auto)
#  4. pick       → Choisir l'appareil dans la liste
#  5. confirm    → Confirmer / nommer l'appareil
# ─────────────────────────────────────────────

class NoCLoudTuyaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config Flow avec QR Code Tuya."""

    VERSION = 2

    def __init__(self) -> None:
        self._cloud: TuyaCloudAuth | None = None
        self._qr_code: str = ""
        self._devices: list[dict] = []
        self._selected: dict = {}
        self._local_ips: dict[str, str] = {}

    # ──────────────────────────────
    #  ÉTAPE 1 — Identifiants Cloud
    # ──────────────────────────────
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape 1 : saisie Client ID / Secret / Région."""
        errors: dict[str, str] = {}

        if user_input is not None:
            client_id = user_input[CONF_CLIENT_ID].strip()
            client_secret = user_input[CONF_CLIENT_SECRET].strip()
            region = user_input[CONF_REGION]

            self._cloud = TuyaCloudAuth(client_id, client_secret, region)

            try:
                await self.hass.async_add_executor_job(self._cloud.get_client_token)
                qr_data = await self.hass.async_add_executor_job(
                    self._cloud.generate_qr_code
                )
                self._qr_code = qr_data["qr_code"]
                return await self.async_step_qr_code()
            except ConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Erreur auth Tuya Cloud")
                errors["base"] = "unknown"

        region_options = {k: f"{v} ({k})" for k, v in TUYA_REGIONS.items()}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_CLIENT_ID):     str,
                vol.Required(CONF_CLIENT_SECRET): str,
                vol.Required(CONF_REGION, default="eu"): vol.In(region_options),
            }),
            description_placeholders={
                "iot_url": "https://iot.tuya.com",
            },
            errors=errors,
        )

    # ──────────────────────────────
    #  ÉTAPE 2 — Afficher QR Code
    # ──────────────────────────────
    async def async_step_qr_code(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape 2 : affiche le QR code à scanner avec Smart Life."""
        if user_input is not None:
            # L'utilisateur clique "Suivant" après avoir scanné
            return await self.async_step_qr_wait()

        return self.async_show_form(
            step_id="qr_code",
            data_schema=vol.Schema({}),
            description_placeholders={
                "qr_code": self._qr_code,
                "app_name": "Smart Life ou Tuya Smart",
            },
        )

    # ──────────────────────────────
    #  ÉTAPE 3 — Poll scan QR
    # ──────────────────────────────
    async def async_step_qr_wait(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape 3 : vérifie si le QR a été scanné, récupère les appareils."""
        errors: dict[str, str] = {}

        # Poll jusqu'à 60s (30 × 2s)
        result = None
        for _ in range(30):
            result = await self.hass.async_add_executor_job(
                self._cloud.poll_qr_scan, self._qr_code
            )
            if result:
                break
            await asyncio.sleep(2)

        if not result:
            errors["base"] = "qr_timeout"
            return self.async_show_form(
                step_id="qr_code",
                data_schema=vol.Schema({}),
                description_placeholders={
                    "qr_code": self._qr_code,
                    "app_name": "Smart Life ou Tuya Smart",
                },
                errors=errors,
            )

        # Récupérer appareils + scanner IPs locales en parallèle
        try:
            devices_task = self.hass.async_add_executor_job(self._cloud.get_devices)
            scan_task    = self.hass.async_add_executor_job(
                TuyaCloudAuth.scan_local_network, 6
            )
            self._devices, self._local_ips = await asyncio.gather(devices_task, scan_task)
        except Exception:
            _LOGGER.exception("Erreur récupération appareils")
            errors["base"] = "unknown"
            return self.async_show_form(step_id="qr_code", data_schema=vol.Schema({}),
                                        description_placeholders={"qr_code": self._qr_code,
                                                                   "app_name": "Smart Life"},
                                        errors=errors)

        if not self._devices:
            errors["base"] = "no_devices"
            return self.async_show_form(step_id="qr_code", data_schema=vol.Schema({}),
                                        description_placeholders={"qr_code": self._qr_code,
                                                                   "app_name": "Smart Life"},
                                        errors=errors)

        return await self.async_step_pick()

    # ──────────────────────────────
    #  ÉTAPE 4 — Choisir l'appareil
    # ──────────────────────────────
    async def async_step_pick(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape 4 : sélection de l'appareil dans la liste."""
        errors: dict[str, str] = {}

        if user_input is not None:
            device_id = user_input["device_id"]
            device = next((d for d in self._devices if d["id"] == device_id), None)
            if device:
                self._selected = device
                return await self.async_step_confirm()
            errors["base"] = "unknown"

        # Construire les options : "Nom (ip) — online/offline"
        options = []
        for d in self._devices:
            ip = self._local_ips.get(d["id"], d.get("ip", "IP inconnue"))
            status = "🟢" if d.get("online") else "🔴"
            label = f"{status} {d['name']}  —  {ip}"
            options.append({"value": d["id"], "label": label})

        return self.async_show_form(
            step_id="pick",
            data_schema=vol.Schema({
                vol.Required("device_id"): SelectSelector(
                    SelectSelectorConfig(
                        options=options,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
            }),
            errors=errors,
        )

    # ──────────────────────────────
    #  ÉTAPE 5 — Confirmer / nommer
    # ──────────────────────────────
    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape 5 : confirmation et nom de l'appareil — tout est pré-rempli."""
        errors: dict[str, str] = {}
        d = self._selected
        ip = self._local_ips.get(d["id"], d.get("ip", ""))

        if user_input is not None:
            await self.async_set_unique_id(d["id"])
            self._abort_if_unique_id_configured()

            # Test connexion locale finale
            try:
                dev = NoCLoudTuyaDevice(
                    host=user_input[CONF_HOST],
                    device_id=d["id"],
                    local_key=d["local_key"],
                    protocol_version=user_input.get(CONF_PROTOCOL_VERSION, DEFAULT_PROTOCOL_VERSION),
                )
                connected = await self.hass.async_add_executor_job(dev.ping)
                if not connected:
                    errors[CONF_HOST] = "cannot_connect"
            except Exception:
                errors[CONF_HOST] = "cannot_connect"

            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={
                        CONF_NAME:             user_input[CONF_NAME],
                        CONF_HOST:             user_input[CONF_HOST],
                        CONF_DEVICE_ID:        d["id"],
                        CONF_LOCAL_KEY:        d["local_key"],
                        CONF_PROTOCOL_VERSION: user_input.get(CONF_PROTOCOL_VERSION, DEFAULT_PROTOCOL_VERSION),
                    },
                )

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME,             default=d["name"]):         str,
                vol.Required(CONF_HOST,             default=ip):                str,
                vol.Optional(CONF_PROTOCOL_VERSION, default=DEFAULT_PROTOCOL_VERSION):
                    vol.In(PROTOCOL_VERSIONS),
            }),
            description_placeholders={
                "device_id":  d["id"],
                "local_key":  d["local_key"][:6] + "••••••",
                "category":   d.get("category", "switch"),
            },
            errors=errors,
        )

    # ──────────────────────────────
    #  Options Flow
    # ──────────────────────────────
    @staticmethod
    def async_get_options_flow(config_entry):
        return NoCLoudTuyaOptionsFlow(config_entry)


class NoCLoudTuyaOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
            }),
        )
