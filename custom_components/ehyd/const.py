"""Constants for the eHYD integration."""

DOMAIN = "ehyd"
INTEGRATION_NAME = "eHYD"
INTEGRATION_DEVICE_MANUFACTURER = "Christian Kadluba (data provided by ehyd.gv.at)"
PLATFORMS = ["sensor"]

RIVER_STATIONS = [
    {"suffix": "schwechat_hallenbad", "hzbnr": 208157},
    {"suffix": "korneuburg", "hzbnr": 207241},
    {"suffix": "fischering", "hzbnr": 213371},
]
RIVER_STATION_NAMETAG = "discharge"
RIVER_STATION_UNIT_OF_MEASUREMENT = "m³/s"

DEFAULT_INTERVAL = 1  # hours, fixed polling interval

CONF_API_KEY = "api_key"

ICON_RIVER_SENSOR = "mdi:waves-arrow-up"
