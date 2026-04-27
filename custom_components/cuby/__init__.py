"""The Cuby (MQTT) integration."""

from __future__ import annotations

import logging

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_DEVICE_ID, CONF_PROTOCOL, DOMAIN, INTER_DEVICE_GAP_S
from .coordinator import CubyDevice, CubyPublishGate

PUBLISH_GATE_KEY = "_publish_gate"

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Cuby device from a config entry."""
    if not await mqtt.async_wait_for_mqtt_client(hass):
        raise ConfigEntryNotReady("MQTT integration is not available")

    domain_data = hass.data.setdefault(DOMAIN, {})
    if PUBLISH_GATE_KEY not in domain_data:
        domain_data[PUBLISH_GATE_KEY] = CubyPublishGate(INTER_DEVICE_GAP_S)

    device = CubyDevice(
        hass=hass,
        entry_id=entry.entry_id,
        device_id=entry.data[CONF_DEVICE_ID],
        protocol=entry.data.get(CONF_PROTOCOL),
        publish_gate=domain_data[PUBLISH_GATE_KEY],
    )
    await device.async_subscribe()

    domain_data[entry.entry_id] = device

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        device: CubyDevice = hass.data[DOMAIN].pop(entry.entry_id)
        await device.async_unload()
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options change so newly-toggled switches/sensors appear."""
    await hass.config_entries.async_reload(entry.entry_id)
