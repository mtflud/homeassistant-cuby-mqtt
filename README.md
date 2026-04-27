# Cuby (MQTT) — Home Assistant integration

A Home Assistant custom integration to control [Cuby](https://cuby.mx/collections/cuby) AC controllers (Arteko Electronics) over MQTT. Ported from [`homebridge-cuby-mqtt`](https://github.com/mtflud/homebridge-cuby).

Supported models: G3 (200) and G4 (400).

## Features

- **Climate entity** with cool / heat / auto / dry / fan-only / off modes
- **Fan speed** (auto / low / medium / high)
- **Target temperature** (16–30 °C)
- **Swing** (vertical vane on/off)
- **Current temperature & humidity** sensors
- **Signal strength** diagnostic sensor
- Optional **Display / Turbo / Long / Eco** switches per device

## Requirements

- Home Assistant 2024.1 or newer
- The built-in **MQTT** integration configured and connected to the same broker your Cuby device publishes to (typically Mosquitto running on the same Home Assistant host)
- Your Cuby device(s) configured to publish to that broker on the `cuby/<device-id>/...` topics

## Installation via HACS

1. In Home Assistant, open **HACS → Integrations → ⋮ → Custom repositories**.
2. Add this repository's URL with category **Integration**.
3. Search for **Cuby (MQTT)** in HACS and install it.
4. Restart Home Assistant.
5. Go to **Settings → Devices & Services → Add Integration** and choose **Cuby (MQTT)**.
6. Enter your Cuby device ID. To add more devices, run the flow again.

## Manual installation

Copy the `custom_components/cuby/` folder into your Home Assistant `config/custom_components/` directory and restart Home Assistant.

## Configuration

The integration uses the Home Assistant MQTT integration — there is no broker / username / password to enter here. Make sure MQTT is set up first.

When adding a device:

| Field | Required | Notes |
|-------|----------|-------|
| Device ID | yes | The Cuby device ID (e.g. `b8d61abbe194`) |
| Protocol | no | Numeric protocol override; only set if you previously had to set it in the Homebridge plugin |

After adding, click **Configure** on the integration card to toggle:

- Display switch
- Turbo switch
- Long switch
- Eco switch
- Humidity sensor (on by default)

## MQTT topics used

| Direction | Topic | Purpose |
|-----------|-------|---------|
| in (subscribe) | `cuby/<id>/out/data` | Telemetry (temperature, humidity, RSSI, …) |
| in (subscribe) | `cuby/<id>/out/state` | Reported AC state |
| out (publish) | `cuby/<id>/in/cmd` | Commands |

## Disclaimer

All product and company names are trademarks™ or registered® trademarks of their respective holders. Use of them does not imply any affiliation with or endorsement by them.
