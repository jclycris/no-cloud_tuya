"""Wrapper tinytuya — communication locale No-Cloud Tuya."""
from __future__ import annotations

import logging
from typing import Any

try:
    import tinytuya
except ImportError as e:
    raise ImportError(
        "La bibliothèque tinytuya est requise. "
        "Installez-la via : pip install tinytuya"
    ) from e

from .const import DP_SWITCH

_LOGGER = logging.getLogger(__name__)


class NoCLoudTuyaDevice:
    """Représente un appareil Tuya en communication locale (sans cloud)."""

    def __init__(
        self,
        host: str,
        device_id: str,
        local_key: str,
        protocol_version: str = "3.3",
    ) -> None:
        self._host = host
        self._device_id = device_id
        self._local_key = local_key
        self._protocol_version = protocol_version
        self._device: tinytuya.OutletDevice | None = None

    def _get_device(self) -> tinytuya.OutletDevice:
        """Retourne (ou crée) l'objet tinytuya."""
        if self._device is None:
            self._device = tinytuya.OutletDevice(
                dev_id=self._device_id,
                address=self._host,
                local_key=self._local_key,
                version=float(self._protocol_version),
            )
            self._device.set_socketPersistent(False)
            self._device.set_socketRetryLimit(2)
            self._device.set_socketTimeout(5)
        return self._device

    def ping(self) -> bool:
        """Tente une connexion test pour valider IP + clé."""
        try:
            dev = self._get_device()
            status = dev.status()
            if "Error" in status:
                _LOGGER.warning("Ping Tuya erreur : %s", status)
                return False
            return True
        except Exception as e:
            _LOGGER.error("Ping Tuya échoué : %s", e)
            raise

    def get_status(self) -> dict[str, Any]:
        """Récupère le statut complet de l'appareil (tous les DPs)."""
        try:
            dev = self._get_device()
            result = dev.status()
            if "Error" in result:
                raise ConnectionError(f"Erreur Tuya : {result['Error']}")
            return result.get("dps", {})
        except Exception as e:
            _LOGGER.error("get_status échoué pour %s : %s", self._host, e)
            # Force recréation de l'objet au prochain appel
            self._device = None
            raise

    def set_switch(self, state: bool, dp: int = DP_SWITCH) -> bool:
        """Allume ou éteint le switch (DP1 par défaut)."""
        try:
            dev = self._get_device()
            result = dev.set_value(dp, state)
            if result and "Error" in result:
                _LOGGER.error("set_switch erreur : %s", result)
                return False
            return True
        except Exception as e:
            _LOGGER.error("set_switch échoué : %s", e)
            self._device = None
            return False

    def turn_on(self) -> bool:
        """Allume l'appareil."""
        return self.set_switch(True)

    def turn_off(self) -> bool:
        """Éteint l'appareil."""
        return self.set_switch(False)

    @property
    def host(self) -> str:
        return self._host

    @property
    def device_id(self) -> str:
        return self._device_id
