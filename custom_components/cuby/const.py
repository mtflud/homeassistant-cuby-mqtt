"""Constants for the Cuby MQTT integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "cuby"
MANUFACTURER: Final = "Arteko Electronics"

# Config keys
CONF_DEVICE_ID: Final = "device_id"
CONF_PROTOCOL: Final = "protocol"

# Options keys
OPT_DISPLAY_SWITCH: Final = "display_switch"
OPT_TURBO_SWITCH: Final = "turbo_switch"
OPT_LONG_SWITCH: Final = "long_switch"
OPT_ECO_SWITCH: Final = "eco_switch"
OPT_HUMIDITY_SENSOR: Final = "humidity_sensor"

# MQTT topics
TOPIC_OUT_DATA: Final = "cuby/{device_id}/out/data"
TOPIC_OUT_STATE: Final = "cuby/{device_id}/out/state"
TOPIC_IN_CMD: Final = "cuby/{device_id}/in/cmd"

# Temperature limits (°C)
MIN_TEMPERATURE_C: Final = 16
MAX_TEMPERATURE_C: Final = 30

# Command debounce window (seconds) — batches rapid characteristic changes into a single publish
COMMAND_DEBOUNCE_S: Final = 0.1

# Dispatcher signal template
SIGNAL_DEVICE_UPDATE: Final = "cuby_device_update_{device_id}"


# AC modes (Cuby protocol values)
class ACMode:
    COOL = "cool"
    HEAT = "heat"
    FAN = "fan"
    DRY = "dry"
    AUTO = "auto"


# Fan modes
class FanMode:
    LOW = "low"
    MEDIUM = "med"
    HIGH = "high"
    AUTO = "auto"


# Vertical vane modes
class VerticalVaneMode:
    TOP = "top"
    TOP_CENTER = "topcenter"
    CENTER = "center"
    BOTTOM_CENTER = "botcenter"
    BOTTOM = "bot"
    AUTO = "auto"
    OFF = "off"


# On/Off
class OnOff:
    ON = "on"
    OFF = "off"
