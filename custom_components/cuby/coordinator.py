"""Per-device state holder + MQTT bridge for Cuby devices."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from homeassistant.components import mqtt
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    COMMAND_DEBOUNCE_S,
    SIGNAL_DEVICE_UPDATE,
    TOPIC_IN_CMD,
    TOPIC_OUT_DATA,
    TOPIC_OUT_STATE,
    ACMode,
    FanMode,
    OnOff,
    VerticalVaneMode,
)

_LOGGER = logging.getLogger(__name__)


class CubyDevice:
    """Holds state for one Cuby device and brokers MQTT traffic for it."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        device_id: str,
        protocol: int | None,
    ) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.device_id = device_id
        self.protocol = protocol

        # AC state — what the AC is set to (mirrors ACState in the Homebridge plugin)
        self.ac_state: dict[str, Any] = {
            "power": OnOff.OFF,
            "mode": ACMode.COOL,
            "fan": FanMode.MEDIUM,
            "temperature": 24,
            "vertical": VerticalVaneMode.AUTO,
            "display": OnOff.ON,
            "turbo": OnOff.OFF,
            "long": OnOff.OFF,
            "eco": OnOff.OFF,
        }

        # Telemetry — what the AC reports (mirrors DeviceState)
        self.device_state: dict[str, Any] = {
            "ambient_temperature": None,
            "ambient_humidity": None,
            "rssi": None,
            "uptime": None,
        }

        self.available: bool = False

        self._unsub_callbacks: list = []
        self._pending_command: dict[str, Any] = {}
        self._debounce_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()

    @property
    def signal(self) -> str:
        return SIGNAL_DEVICE_UPDATE.format(device_id=self.device_id)

    async def async_subscribe(self) -> None:
        """Subscribe to the device's MQTT topics."""

        @callback
        def _message_received(msg: mqtt.ReceiveMessage) -> None:
            try:
                payload = json.loads(msg.payload) if msg.payload else {}
            except (ValueError, TypeError) as err:
                _LOGGER.warning(
                    "Cuby %s: invalid JSON on %s: %s", self.device_id, msg.topic, err
                )
                return

            if not isinstance(payload, dict):
                return

            # Both topics carry overlapping fields — merge into both stores
            self.ac_state.update(
                {k: v for k, v in payload.items() if k in self.ac_state}
            )
            self.device_state.update(
                {k: v for k, v in payload.items() if k in self.device_state}
            )

            self.available = True
            async_dispatcher_send(self.hass, self.signal)

        self._unsub_callbacks.append(
            await mqtt.async_subscribe(
                self.hass,
                TOPIC_OUT_DATA.format(device_id=self.device_id),
                _message_received,
                qos=0,
            )
        )
        self._unsub_callbacks.append(
            await mqtt.async_subscribe(
                self.hass,
                TOPIC_OUT_STATE.format(device_id=self.device_id),
                _message_received,
                qos=0,
            )
        )

    async def async_unload(self) -> None:
        """Tear down subscriptions."""
        for unsub in self._unsub_callbacks:
            unsub()
        self._unsub_callbacks.clear()

        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()
            try:
                await self._debounce_task
            except asyncio.CancelledError:
                pass

    async def async_send(self, command: dict[str, Any]) -> None:
        """Queue a command; commands sent within a short window are merged into one publish."""
        async with self._lock:
            self._pending_command.update(command)
            if self._debounce_task is None or self._debounce_task.done():
                self._debounce_task = self.hass.async_create_task(self._flush())

    async def _flush(self) -> None:
        await asyncio.sleep(COMMAND_DEBOUNCE_S)
        async with self._lock:
            if not self._pending_command:
                return
            payload = dict(self._pending_command)
            self._pending_command.clear()

        if self.protocol is not None:
            payload["protocol"] = self.protocol

        topic = TOPIC_IN_CMD.format(device_id=self.device_id)
        _LOGGER.debug("Cuby %s -> %s: %s", self.device_id, topic, payload)

        await mqtt.async_publish(self.hass, topic, json.dumps(payload), qos=0)

        # Optimistic update so the UI reflects the change immediately
        for key, value in payload.items():
            if key in self.ac_state:
                self.ac_state[key] = value
        async_dispatcher_send(self.hass, self.signal)
