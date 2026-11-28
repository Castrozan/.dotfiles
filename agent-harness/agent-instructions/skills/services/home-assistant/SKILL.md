---
name: home-assistant
description: Control home lights and AC via the ha-light and ha-ac CLIs, including Tuya and Midea outage recovery. Use for lights, AC, temperature, or Home Assistant requests.
---

### Commands

Control lights with `ha-light` and the air conditioner with `ha-ac`. Run either without arguments for usage.

### Architecture

Home Assistant serves localhost:8123. The `home-assistant` flake input declares its container runtime.
Its two integrations are Tuya (lights, cloud-based) and Midea AC LAN (air conditioner, local LAN).
CLI scripts use the HA REST API with a long-lived token from agenix. Web UI credentials are in the password store
under `home-assistant/admin`. Verify the systemd service name from the NixOS module before restarting.

### Device constraints

Lights support color temperature only. Create new scenes in Tuya/Smart Life before activating them in Home Assistant.
The AC communicates over the local LAN.
The climate entity embeds the Midea device ID. After re-pairing, update `homeAssistant.airConditionerEntityId` on chise.

### Troubleshooting

Lights unavailable but working from the phone app: the Tuya cloud auth token expired. Check the config entries API for
`tuya setup_error`. Fix by opening the integrations dashboard in the HA web UI, clicking Reconfigure on the Tuya entry,
and scanning the QR code with the Smart Life or Tuya Smart phone app. This needs the user to scan with their phone.

AC unavailable: the LAN IP likely changed. Run `ha-ac-recover-ip`. The toggle script calls recovery automatically.

Web UI password lost: the auth provider storage file under HA's config directory holds bcrypt-hashed passwords. Generate
a new bcrypt hash (needs the bcrypt Python package via nix-shell), write it to that file, restart the HA service, and
update the password store.

### Traps

The Midea integration needs the `midea-local` pip package inside the container, and image updates drop pip packages
unless the config volume is mounted. Service calls (turn_on, set_temperature) return an empty body; only state queries
return JSON, so do not treat an empty response to a command as a failure.

### Adding devices

New Tuya devices appear after pairing in the Smart Life app; HA picks them up on reload, but re-authenticate first if
Tuya auth is expired. New Midea devices need auto-discovery through the config flow in HA. Both scripts follow identical
patterns, so read existing code before modifying.
