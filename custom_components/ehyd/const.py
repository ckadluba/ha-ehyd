"""Constants for the eHYD integration."""

DOMAIN = "ehyd"
DATA_COORDINATOR = "coordinator"
INTEGRATION_NAME = "eHYD"
INTEGRATION_DEVICE_MANUFACTURER = (
    "Christian Kadluba (data provided by ehyd.gv.at; unverified raw data)"
)
PLATFORMS = ["sensor"]

RIVER_STATION_NAMETAG = "discharge"
RIVER_STATION_UNIT_OF_MEASUREMENT = "m³/s"

GROUNDWATER_STATION_NAMETAG = "elevation"
GROUNDWATER_STATION_UNIT_OF_MEASUREMENT = "m a.s.l."

DEFAULT_INTERVAL = 1  # hours, fixed polling interval

CONF_SELECTED_STATIONS = "selected_stations"
CONF_STATION_TYPE = "station_type"
STATION_TYPE_GROUNDWATER = "groundwater"
STATION_TYPE_RIVER = "river"
COORDINATOR = "coordinator"
SETUP_LOCK = "setup_lock"

ICON_RIVER_SENSOR = "mdi:waves-arrow-up"
ICON_GROUNDWATER_SENSOR = "mdi:altimeter"
