"""Constants for the eHYD integration."""

DOMAIN = "ehyd"
DATA_COORDINATOR = "coordinator"
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

GROUNDWATER_STATIONS = [
    {"suffix": "leobersdorf_bl_451", "hzbnr": 300699},
    {"suffix": "langenzersdorf_br_2112", "hzbnr": 313221},
]
GROUNDWATER_STATION_NAMETAG = "elevation"
GROUNDWATER_STATION_UNIT_OF_MEASUREMENT = "m a.s.l"

DEFAULT_INTERVAL = 1  # hours, fixed polling interval

CONF_SELECTED_STATIONS = "selected_stations"

ICON_RIVER_SENSOR = "mdi:waves-arrow-up"
ICON_GROUNDWATER_SENSOR = "mdi:altimeter"
