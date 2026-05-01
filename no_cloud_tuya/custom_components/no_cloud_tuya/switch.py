"""Plateforme Switch — No-Cloud Tuya."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_NAME, CONF_DEVICE_ID, DP_SWITCH
from .coordinator import NoCLoudTuyaCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialise les entités switch pour cette entrée."""
    coordinator: NoCLoudTuyaCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [NoCLoudTuyaSwitch(coordinator, entry)],
        update_before_add=True,
    )


class NoCLoudTuyaSwitch(CoordinatorEntity, SwitchEntity):
    """Entité switch Tuya — communication locale uniquement."""

    _attr_has_entity_name = True
    _attr_name = None  # Utilise le nom du device

    def __init__(
        self,
        coordinator: NoCLoudTuyaCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._device_id = entry.data[CONF_DEVICE_ID]
        self._device_name = entry.data.get(CONF_NAME, "Prise Tuya")

        # Identifiant unique stable
        self._attr_unique_id = f"{self._device_id}_switch"

        # Informations sur le device (affichées dans HA)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=self._device_name,
            manufacturer="Tuya",
            model="Smart Switch / Prise",
        )

    @property
    def is_on(self) -> bool | None:
        """Retourne True si l'appareil est allumé."""
        if self.coordinator.data is None:
            return None
        # DP 1 = état principal on/off
        return bool(self.coordinator.data.get(DP_SWITCH, False))

    @property
    def available(self) -> bool:
        """Retourne True si le coordinateur a des données valides."""
        return self.coordinator.last_update_success

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Allume l'appareil."""
        success = await self.hass.async_add_executor_job(
            self.coordinator.device.turn_on
        )
        if success:
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Éteint l'appareil."""
        success = await self.hass.async_add_executor_job(
            self.coordinator.device.turn_off
        )
        if success:
            await self.coordinator.async_request_refresh()
