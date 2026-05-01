"""Coordinator — No-Cloud Tuya."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONF_PROTOCOL_VERSION,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_PROTOCOL_VERSION,
)
from .tuya_device import NoCLoudTuyaDevice

_LOGGER = logging.getLogger(__name__)


class NoCLoudTuyaCoordinator(DataUpdateCoordinator):
    """Coordinator qui interroge l'appareil Tuya localement à intervalle régulier."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.device = NoCLoudTuyaDevice(
            host=entry.data[CONF_HOST],
            device_id=entry.data[CONF_DEVICE_ID],
            local_key=entry.data[CONF_LOCAL_KEY],
            protocol_version=entry.data.get(CONF_PROTOCOL_VERSION, DEFAULT_PROTOCOL_VERSION),
        )

        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.data[CONF_DEVICE_ID]}",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict:
        """Interroge l'appareil et retourne les DPs."""
        try:
            dps = await self.hass.async_add_executor_job(self.device.get_status)
            return dps
        except ConnectionError as err:
            raise UpdateFailed(f"Connexion impossible à l'appareil Tuya : {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Erreur inattendue : {err}") from err
