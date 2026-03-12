---
name: home-assistant
description: Control smart home devices via Home Assistant — lights (ha-light) and air conditioner (ha-ac). Use when user asks to turn on/off lights or AC, change temperature, brightness, fan speed, or check device status.
---

<architecture>
Home Assistant runs as a Docker container on localhost:8123. Two integrations: Tuya (lights) and Midea AC LAN (air conditioner via custom component). CLI scripts use the HA REST API with a long-lived token managed by agenix. Scripts have built-in usage — run them without args for help.
</architecture>

<device_constraints>
Lights are color_temp mode only — no RGB. Scenes are managed in the Tuya/Smart Life app, not in code — HA just activates them. New scenes must be created in the app first.

The AC communicates locally over LAN, not cloud. The Midea AC entity ID includes the device's numeric ID — if the device is re-paired, the entity ID changes and the script constant must be updated.
</device_constraints>

<traps>
The Midea integration requires the `midea-local` pip package inside the HA Docker container. On container recreation (image update), custom components and pip packages are lost unless `/config` is volume-mounted.

The HA REST API returns empty body for service calls (turn_on, set_temperature, etc.) — only state queries return JSON. Do not assume all API calls return data.
</traps>

<adding_devices>
New Tuya devices appear automatically after pairing in Smart Life app — HA picks them up on reload. Add entity IDs to the script constants.

New Midea devices: run auto-discovery through the midea_ac_lan config flow in HA. Requires SmartHome account credentials. Update the entity ID constant in the script.

Read existing script code before modifying — both scripts follow identical patterns.
</adding_devices>
