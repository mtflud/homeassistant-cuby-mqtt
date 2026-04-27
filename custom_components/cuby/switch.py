"""Optional Cuby switches: display, turbo, long, eco."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    MANUFACTURER,
    OPT_DISPLAY_SWITCH,
    OPT_ECO_SWITCH,
    OPT_LONG_SWITCH,
    OPT_TURBO_SWITCH,
    OnOff,
)
from .coordinator import CubyDevice

# (option-key, ac_state-key, label)
SWITCH_DEFS = [
    (OPT_DISPLAY_SWITCH, "display", "Display"),
    (OPT_TURBO_SWITCH, "turbo", "Turbo"),
    (OPT_LONG_SWITCH, "long", "Long"),
    (OPT_ECO_SWITCH, "eco", "Eco"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    device: CubyDevice = hass.data[DOMAIN][entry.entry_id]
    entities = [
        CubySwitch(device, state_key, label)
        for opt_key, state_key, label in SWITCH_DEFS
        if entry.options.get(opt_key)
    ]
    if entities:
        async_add_entities(entities)


class CubySwitch(SwitchEntity):
    """Toggle a Cuby AC mode (display/turbo/long/eco)."""

    _attr_has_entity_name = True

    def __init__(self, device: CubyDevice, state_key: str, label: str) -> None:
        self._device = device
        self._key = state_key
        self._attr_name = label
        self._attr_unique_id = f"{device.device_id}_{state_key}"
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
    def is_on(self) -> bool:
        return self._device.ac_state.get(self._key) == OnOff.ON

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._device.async_send({self._key: OnOff.ON})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._device.async_send({self._key: OnOff.OFF})
