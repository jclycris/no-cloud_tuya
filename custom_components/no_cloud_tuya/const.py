"""Constantes No-Cloud Tuya."""

DOMAIN = "no_cloud_tuya"

# Clés de configuration — appareil
CONF_HOST = "host"
CONF_DEVICE_ID = "device_id"
CONF_LOCAL_KEY = "local_key"
CONF_PROTOCOL_VERSION = "protocol_version"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_NAME = "name"

# Clés de configuration — QR / Cloud auth
CONF_REGION = "region"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"

# Valeurs par défaut
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_PROTOCOL_VERSION = "3.3"

PROTOCOL_VERSIONS = ["3.1", "3.3", "3.4", "3.5"]

# Régions Tuya IoT Cloud
TUYA_REGIONS = {
    "eu":   "Europe",
    "us":   "Amérique du Nord",
    "cn":   "Chine",
    "in":   "Inde",
    "us-e": "Amérique (Est)",
    "eu-w": "Europe (Ouest)",
    "sg":   "Asie-Pacifique",
}

# URL de base par région
TUYA_API_BASE = {
    "eu":   "https://openapi.tuyaeu.com",
    "us":   "https://openapi.tuyaus.com",
    "cn":   "https://openapi.tuyacn.com",
    "in":   "https://openapi.tuyain.com",
    "us-e": "https://openapi-ueaz.tuyaus.com",
    "eu-w": "https://openapi-weaz.tuyaeu.com",
    "sg":   "https://openapi.tuyasg.com",
}

# Data Points Tuya standard
DP_SWITCH = 1
DP_CURRENT = 4
DP_POWER = 5
DP_VOLTAGE = 6
