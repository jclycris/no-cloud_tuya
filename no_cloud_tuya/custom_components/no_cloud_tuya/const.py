"""Constantes No-Cloud Tuya."""

DOMAIN = "no_cloud_tuya"

# Clés de configuration
CONF_HOST = "host"
CONF_DEVICE_ID = "device_id"
CONF_LOCAL_KEY = "local_key"
CONF_PROTOCOL_VERSION = "protocol_version"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_NAME = "name"

# Valeurs par défaut
DEFAULT_SCAN_INTERVAL = 30          # secondes
DEFAULT_PROTOCOL_VERSION = "3.3"

PROTOCOL_VERSIONS = ["3.1", "3.3", "3.4", "3.5"]

# DP (Data Point) standard pour switch/prise Tuya
DP_SWITCH = 1        # DP 1 = état on/off principal
DP_CURRENT = 4       # DP 4 = courant (mA) — si la prise le supporte
DP_POWER = 5         # DP 5 = puissance (W)
DP_VOLTAGE = 6       # DP 6 = tension (V)
