"""Cuby climate (HeaterCooler) entity."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, PRECISION_WHOLE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    MANUFACTURER,
    MAX_TEMPERATURE_C,
    MIN_TEMPERATURE_C,
    ACMode,
    FanMode,
    OnOff,
    VerticalVaneMode,
)
from .coordinator import CubyDevice

_LOGGER = logging.getLogger(__name__)

# HA fan modes — keep them human-readable; we map to Cuby values internally
FAN_LOW = "low"
FAN_MEDIUM = "medium"
FAN_HIGH = "high"
FAN_AUTO = "auto"

FAN_MODE_TO_CUBY = {
    FAN_LOW: FanMode.LOW,
    FAN_MEDIUM: FanMode.MEDIUM,
    FAN_HIGH: FanMode.HIGH,
    FAN_AUTO: FanMode.AUTO,
}
CUBY_TO_FAN_MODE = {v: k for k, v in FAN_MODE_TO_CUBY.items()}

HVAC_TO_CUBY = {
    HVACMode.COOL: ACMode.COOL,
    HVACMode.HEAT: ACMode.HEAT,
    HVACMode.FAN_ONLY: ACMode.FAN,
    HVACMode.DRY: ACMode.DRY,
    HVACMode.HEAT_COOL: ACMode.AUTO,
}
CUBY_TO_HVAC = {v: k for k, v in HVAC_TO_CUBY.items()}

SWING_ON = "on"
SWING_OFF = "off"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    device: CubyDevice = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CubyClimate(device)])


class CubyClimate(ClimateEntity):
    """Cuby AC climate entity."""

    _attr_has_entity_name = True
    _attr_name = None  # use device name
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = PRECISION_WHOLE
    _attr_min_temp = MIN_TEMPERATURE_C
    _attr_max_temp = MAX_TEMPERATURE_C
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.COOL,
        HVACMode.HEAT,
        HVACMode.HEAT_COOL,
        HVACMode.DRY,
        HVACMode.FAN_ONLY,
    ]
    _attr_fan_modes = [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]
    _attr_swing_modes = [SWING_OFF, SWING_ON]

    def __init__(self, device: CubyDevice) -> None:
        self._device = device
        self._attr_unique_id = f"{device.device_id}_climate"
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

    @property
    def current_temperature(self) -> float | None:
        value = self._device.device_state.get("ambient_temperature")
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def current_humidity(self) -> int | None:
        value = self._device.device_state.get("ambient_humidity")
        try:
            return int(float(value)) if value is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def target_temperature(self) -> float | None:
        try:
            return float(self._device.ac_state.get("temperature"))
        except (TypeError, ValueError):
            return None

    @property
    def hvac_mode(self) -> HVACMode:
        if self._device.ac_state.get("power") != OnOff.ON:
            return HVACMode.OFF
        return CUBY_TO_HVAC.get(
            self._device.ac_state.get("mode"), HVACMode.HEAT_COOL
        )

    @property
    def fan_mode(self) -> str | None:
        return CUBY_TO_FAN_MODE.get(self._device.ac_state.get("fan"), FAN_AUTO)

    @property
    def swing_mode(self) -> str:
        if self._device.ac_state.get("vertical") == VerticalVaneMode.OFF:
            return SWING_OFF
        return SWING_ON

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self._device.async_send({"power": OnOff.OFF})
            return

        cuby_mode = HVAC_TO_CUBY.get(hvac_mode)
        command: dict[str, Any] = {"power": OnOff.ON}
        if cuby_mode is not None:
            command["mode"] = cuby_mode
        await self._device.async_send(command)

    async def async_turn_on(self) -> None:
        await self._device.async_send({"power": OnOff.ON})

    async def async_turn_off(self) -> None:
        await self._device.async_send({"power": OnOff.OFF})

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        target = max(MIN_TEMPERATURE_C, min(MAX_TEMPERATURE_C, int(round(temperature))))
        await self._device.async_send({"temperature": target})

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        cuby_fan = FAN_MODE_TO_CUBY.get(fan_mode)
        if cuby_fan is None:
            return
        await self._device.async_send({"fan": cuby_fan})

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        value = (
            VerticalVaneMode.AUTO if swing_mode == SWING_ON else VerticalVaneMode.OFF
        )
        await self._device.async_send({"vertical": value})
