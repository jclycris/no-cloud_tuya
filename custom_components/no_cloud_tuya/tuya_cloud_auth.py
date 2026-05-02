"""Authentification Tuya Cloud via QR Code — No-Cloud Tuya.

Flow :
  1. L'utilisateur saisit Client ID + Secret + Région (depuis iot.tuya.com)
  2. On génère un QR code Tuya (scan_code unique)
  3. L'utilisateur scanne avec l'app Smart Life / Tuya Smart
  4. On poll l'API jusqu'à confirmation du scan
  5. On récupère le token utilisateur + la liste des appareils avec leurs Local Keys
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from typing import Any

import requests

from .const import TUYA_API_BASE

_LOGGER = logging.getLogger(__name__)

SCAN_POLL_INTERVAL = 2   # secondes entre chaque poll
SCAN_TIMEOUT = 120        # secondes max pour scanner le QR


class TuyaCloudAuth:
    """Client d'authentification Tuya Cloud par QR code."""

    def __init__(self, client_id: str, client_secret: str, region: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.region = region
        self.base_url = TUYA_API_BASE.get(region, TUYA_API_BASE["eu"])
        self._token: str | None = None
        self._uid: str | None = None

    # ------------------------------------------------------------------ #
    #  Signature HMAC-SHA256 Tuya
    # ------------------------------------------------------------------ #
    def _sign(self, t: str, access_token: str = "") -> str:
        msg = self.client_id + access_token + t
        return hmac.new(
            self.client_secret.encode("utf-8"),
            msg.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest().upper()

    def _headers(self, access_token: str = "") -> dict:
        t = str(int(time.time() * 1000))
        return {
            "client_id": self.client_id,
            "sign": self._sign(t, access_token),
            "sign_method": "HMAC-SHA256",
            "t": t,
            "access_token": access_token,
            "lang": "en",
        }

    # ------------------------------------------------------------------ #
    #  Étape 1 : Token d'accès client (sans user)
    # ------------------------------------------------------------------ #
    def get_client_token(self) -> str:
        """Récupère un token d'accès client (grant_type=1)."""
        url = f"{self.base_url}/v1.0/token?grant_type=1"
        resp = requests.get(url, headers=self._headers(), timeout=10)
        data = resp.json()
        if not data.get("success"):
            raise ConnectionError(f"Token client échoué : {data}")
        token = data["result"]["access_token"]
        self._token = token
        return token

    # ------------------------------------------------------------------ #
    #  Étape 2 : Générer le QR Code (scan_code)
    # ------------------------------------------------------------------ #
    def generate_qr_code(self) -> dict:
        """Génère un scan_code Tuya et retourne {'qr_code': url, 'expire_time': int}."""
        token = self._token or self.get_client_token()
        url = f"{self.base_url}/v1.0/iot-03/users/login/qrcode"
        payload = {
            "client_id": self.client_id,
            "expire_time": SCAN_TIMEOUT,
        }
        resp = requests.post(
            url,
            headers={**self._headers(token), "Content-Type": "application/json"},
            json=payload,
            timeout=10,
        )
        data = resp.json()
        if not data.get("success"):
            # Fallback : certaines régions utilisent un autre endpoint
            url2 = f"{self.base_url}/v1.0/users/login/qrcode"
            resp = requests.post(
                url2,
                headers={**self._headers(token), "Content-Type": "application/json"},
                json=payload,
                timeout=10,
            )
            data = resp.json()
        if not data.get("success"):
            raise ConnectionError(f"Génération QR échouée : {data}")
        result = data.get("result", {})
        return {
            "qr_code": result.get("qrcode", result.get("url", "")),
            "expire_time": result.get("expire_time", SCAN_TIMEOUT),
        }

    # ------------------------------------------------------------------ #
    #  Étape 3 : Vérifier si le QR a été scanné
    # ------------------------------------------------------------------ #
    def poll_qr_scan(self, qr_code: str) -> dict | None:
        """Poll le résultat du scan. Retourne le token user si OK, None sinon."""
        token = self._token or self.get_client_token()
        url = f"{self.base_url}/v1.0/iot-03/users/login/qrcode/result"
        params = {"qrcode": qr_code}
        resp = requests.get(
            url,
            headers=self._headers(token),
            params=params,
            timeout=10,
        )
        data = resp.json()
        if data.get("success") and data.get("result"):
            result = data["result"]
            # Stocker le token utilisateur
            user_token = result.get("access_token") or result.get("token")
            if user_token:
                self._token = user_token
                self._uid = result.get("uid")
                return result
        return None

    # ------------------------------------------------------------------ #
    #  Étape 4 : Récupérer les appareils + Local Keys
    # ------------------------------------------------------------------ #
    def get_devices(self) -> list[dict]:
        """Récupère tous les appareils avec leurs local keys."""
        if not self._token:
            raise RuntimeError("Non authentifié. Scannez d'abord le QR code.")

        # Récupérer le UID si pas encore fait
        uid = self._uid
        if not uid:
            uid = self._get_uid()

        url = f"{self.base_url}/v1.0/users/{uid}/devices"
        resp = requests.get(
            url,
            headers=self._headers(self._token),
            timeout=10,
        )
        data = resp.json()
        if not data.get("success"):
            # Fallback endpoint v2
            url = f"{self.base_url}/v2.0/cloud/thing/device"
            resp = requests.get(url, headers=self._headers(self._token), timeout=10)
            data = resp.json()

        if not data.get("success"):
            raise ConnectionError(f"Récupération appareils échouée : {data}")

        devices = data.get("result", [])
        if isinstance(devices, dict):
            devices = devices.get("devices", devices.get("list", []))

        return [
            {
                "id":        d.get("id", d.get("dev_id", "")),
                "name":      d.get("name", "Appareil inconnu"),
                "local_key": d.get("local_key", d.get("key", "")),
                "ip":        d.get("ip", ""),
                "category":  d.get("category", ""),
                "version":   str(d.get("sub", False)),
                "online":    d.get("online", False),
            }
            for d in devices
            if d.get("id") or d.get("dev_id")
        ]

    def _get_uid(self) -> str:
        """Récupère le UID utilisateur depuis n'importe quel device ID."""
        url = f"{self.base_url}/v1.0/token/{self._token}"
        resp = requests.get(url, headers=self._headers(self._token), timeout=10)
        data = resp.json()
        uid = data.get("result", {}).get("uid", "")
        self._uid = uid
        return uid

    # ------------------------------------------------------------------ #
    #  Scanner le réseau local pour trouver les IPs
    # ------------------------------------------------------------------ #
    @staticmethod
    def scan_local_network(timeout: int = 8) -> dict[str, str]:
        """Scan LAN et retourne {device_id: ip}."""
        try:
            import tinytuya
            devices = tinytuya.deviceScan(verbose=False, maxretry=timeout)
            return {v.get("gwId", ""): v.get("ip", "") for v in devices.values()}
        except Exception as e:
            _LOGGER.warning("Scan réseau échoué : %s", e)
            return {}
