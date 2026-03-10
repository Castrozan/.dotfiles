---
name: home-assistant
description: Control smart home devices via Home Assistant — lights (ha-light) and air conditioner (ha-ac). Use when user asks to turn on/off lights or AC, change temperature, brightness, fan speed, or check device status.
---

<architecture>
Home Assistant runs as a Docker container (`homeassistant`, image `ghcr.io/home-assistant/home-assistant:stable`) with `--network=host` on `localhost:8123`. Two integrations: Tuya (lights) and Midea AC LAN (air conditioner via custom component). CLI scripts use the HA REST API with a long-lived token stored at `~/.secrets/home-assistant-token` (managed by agenix). Scripts are pure Python with no external dependencies — they use `urllib.request` directly.
</architecture>

<lights>
`ha-light` controls 4 Tuya lights: bedroom, kitchen, livingroom, bathroom.

Commands: `on <target>`, `off <target>`, `status [target]`, `set <target> --brightness N --temp N`, `scene <name>`.
Targets: bedroom, kitchen, livingroom, bathroom, all.
Brightness: 0-255. Color temperature: 2000-6500K. No RGB support — lights are color_temp mode only.

Examples: `ha-light on all --brightness 200 --temp 3500`, `ha-light off bedroom`, `ha-light status`.
</lights>

<air-conditioner>
`ha-ac` controls a Midea AC discovered via the midea_ac_lan custom component. The AC communicates locally over LAN (not cloud).

Commands: `on`, `off`, `status`, `mode <mode>`, `temp <celsius>`, `fan <speed>`, `swing <direction>`, `preset <preset>`, `set [flags]`.
HVAC modes: off, auto, cool, dry, heat, fan_only.
Fan: silent, low, medium, high, full, auto.
Swing: off, vertical, horizontal, both.
Presets: none, comfort, eco, boost, sleep, away.
Temperature: 16-30°C (0.5 step).

The `set` command combines multiple flags: `ha-ac set --temp 22 --fan low --mode cool --swing vertical --preset eco`.
The `status` command shows indoor/target temperature, fan, swing, preset, realtime power (watts), and total energy consumption (kWh).
</air-conditioner>

<traps>
The Midea integration requires the `midea-local` pip package installed inside the HA Docker container. On container recreation (image update), custom components and pip packages are lost unless `/config` is volume-mounted. Verify after updates: `docker exec homeassistant python3 -c "import midealocal"`.

The Midea AC entity ID includes the device's numeric ID, not a friendly name — check `climate.*` entities in HA to find the current entity ID. The script hardcodes this; if the device is re-paired, the entity ID changes and the script must be updated.

Tuya lights use scenes managed in the Tuya/Smart Life app — HA just activates them by `scene.<name>`. New scenes must be created in the app first.

The HA REST API returns empty body for service calls (turn_on, set_temperature, etc.) — only state queries return JSON. The scripts handle this; do not assume all API calls return data.
</traps>

<adding-devices>
New lights: Add entity ID to `ALL_LIGHT_ENTITY_IDS` in the light control script, verify via `ha-light status`. New Tuya devices appear automatically after pairing in Smart Life app — HA's Tuya integration picks them up on reload.

New Midea devices: Run auto-discovery through the midea_ac_lan config flow in HA. Requires SmartHome account credentials. Update the entity ID constant in the AC control script.

The scripts and tests live in the home-assistant module. Read the existing code before modifying — both scripts follow identical patterns for token reading, API requests, and argument parsing.
</adding-devices>

<ha-maintenance>
Container management: `docker restart homeassistant`, `docker exec homeassistant cat /config/home-assistant.log | tail -50`.
API health: `curl -sf http://localhost:8123/api/ -H "Authorization: Bearer $(cat ~/.secrets/home-assistant-token)"`.
List all entities: query `/api/states` and filter by domain (light.*, climate.*, scene.*).
Config flows for new integrations: POST to `/api/config/config_entries/flow` with `{"handler":"integration_name"}`, then follow the multi-step flow via the returned `flow_id`.
</ha-maintenance>
