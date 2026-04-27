"""Config and options flow for Cuby (MQTT)."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback

from .const import (
    CONF_DEVICE_ID,
    CONF_PROTOCOL,
    DOMAIN,
    OPT_DISPLAY_SWITCH,
    OPT_ECO_SWITCH,
    OPT_HUMIDITY_SENSOR,
    OPT_LONG_SWITCH,
    OPT_TURBO_SWITCH,
)


class CubyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cuby (MQTT)."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add a Cuby device by ID."""
        if not await mqtt.async_wait_for_mqtt_client(self.hass):
            return self.async_abort(reason="mqtt_required")

        errors: dict[str, str] = {}

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID].strip()
            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Cuby {device_id}",
                data={
                    CONF_DEVICE_ID: device_id,
                    CONF_PROTOCOL: user_input.get(CONF_PROTOCOL),
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_ID): str,
                vol.Optional(CONF_PROTOCOL): vol.All(
                    vol.Coerce(int), vol.Range(min=0, max=999)
                ),
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return CubyOptionsFlow()


class CubyOptionsFlow(OptionsFlow):
    """Toggle which optional entities are exposed for this device."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        opts = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    OPT_DISPLAY_SWITCH,
                    default=opts.get(OPT_DISPLAY_SWITCH, False),
                ): bool,
                vol.Optional(
                    OPT_TURBO_SWITCH,
                    default=opts.get(OPT_TURBO_SWITCH, False),
                ): bool,
                vol.Optional(
                    OPT_LONG_SWITCH,
                    default=opts.get(OPT_LONG_SWITCH, False),
                ): bool,
                vol.Optional(
                    OPT_ECO_SWITCH,
                    default=opts.get(OPT_ECO_SWITCH, False),
                ): bool,
                vol.Optional(
                    OPT_HUMIDITY_SENSOR,
                    default=opts.get(OPT_HUMIDITY_SENSOR, True),
                ): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
