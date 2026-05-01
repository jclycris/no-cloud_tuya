"""Config Flow — No-Cloud Tuya."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONF_PROTOCOL_VERSION,
    CONF_SCAN_INTERVAL,
    CONF_NAME,
    DEFAULT_PROTOCOL_VERSION,
    DEFAULT_SCAN_INTERVAL,
    PROTOCOL_VERSIONS,
)
from .tuya_device import NoCLoudTuyaDevice

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default="Prise Tuya"): str,
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_DEVICE_ID): str,
        vol.Required(CONF_LOCAL_KEY): str,
        vol.Optional(CONF_PROTOCOL_VERSION, default=DEFAULT_PROTOCOL_VERSION): vol.In(PROTOCOL_VERSIONS),
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=5, max=300)
        ),
    }
)


class NoCLoudTuyaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gère le flux de configuration de No-Cloud Tuya."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Étape initiale — saisie des paramètres de l'appareil."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Vérification unicité (évite les doublons)
            await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
            self._abort_if_unique_id_configured()

            # Test de connexion locale
            try:
                device = NoCLoudTuyaDevice(
                    host=user_input[CONF_HOST],
                    device_id=user_input[CONF_DEVICE_ID],
                    local_key=user_input[CONF_LOCAL_KEY],
                    protocol_version=user_input[CONF_PROTOCOL_VERSION],
                )
                connected = await self.hass.async_add_executor_job(device.ping)
                if not connected:
                    errors["base"] = "cannot_connect"
            except PermissionError:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Erreur inattendue lors de la connexion Tuya")
                errors["base"] = "unknown"

            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return NoCLoudTuyaOptionsFlow(config_entry)


class NoCLoudTuyaOptionsFlow(config_entries.OptionsFlow):
    """Gère les options (intervalle de rafraîchissement)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=300))
                }
            ),
        )
