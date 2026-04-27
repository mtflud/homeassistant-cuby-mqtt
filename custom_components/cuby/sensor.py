"""Cuby telemetry sensors."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, OPT_HUMIDITY_SENSOR
from .coordinator import CubyDevice


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    device: CubyDevice = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [
        CubyTemperatureSensor(device),
        CubySignalSensor(device),
    ]
    # Humidity defaults to True so users get it by default; matches the spirit
    # of the original plugin's optional humidity sensor (with a saner default for HA).
    if entry.options.get(OPT_HUMIDITY_SENSOR, True):
        entities.append(CubyHumiditySensor(device))

    async_add_entities(entities)


class _CubySensorBase(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, device: CubyDevice) -> None:
        self._device = device
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.device_id)},
            "manufacturer": MANUFACTURER,
            "model": "Cuby",
            "name": f"Cuby {device.device_id}",
        }

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self._device.signal, self._handle_update
            )
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        return self._device.available


class CubyTemperatureSensor(_CubySensorBase):
    _attr_name = "Temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, device: CubyDevice) -> None:
        super().__init__(device)
        self._attr_unique_id = f"{device.device_id}_temperature"

    @property
    def native_value(self) -> float | None:
        value = self._device.device_state.get("ambient_temperature")
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None


class CubyHumiditySensor(_CubySensorBase):
    _attr_name = "Humidity"
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, device: CubyDevice) -> None:
        super().__init__(device)
        self._attr_unique_id = f"{device.device_id}_humidity"

    @property
    def native_value(self) -> float | None:
        value = self._device.device_state.get("ambient_humidity")
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None


class CubySignalSensor(_CubySensorBase):
    _attr_name = "Signal strength"
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, device: CubyDevice) -> None:
        super().__init__(device)
        self._attr_unique_id = f"{device.device_id}_rssi"

    @property
    def native_value(self) -> int | None:
        value = self._device.device_state.get("rssi")
        try:
            return int(float(value)) if value is not None else None
        except (TypeError, ValueError):
            return None
