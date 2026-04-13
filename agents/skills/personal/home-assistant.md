
<architecture>
Home Assistant runs as a Podman container on localhost:8123. Two integrations: Tuya (lights, cloud-based) and Midea AC LAN (air conditioner, local LAN). CLI scripts use the HA REST API with a long-lived token from agenix. Run any script without args for usage. Web UI credentials are in the password store under `home-assistant/admin`. Verify the systemd service name from the NixOS module before restarting - it is not the obvious name.
</architecture>

<device_constraints>
Lights are color_temp only, no RGB. Scenes are managed in the Tuya/Smart Life phone app, not in code - HA only activates them. New scenes must be created in the app first.

The AC communicates over local LAN, not cloud. The Midea entity ID includes the device's numeric ID - if re-paired, the entity ID changes and the script constant must be updated.
</device_constraints>

<troubleshooting>
Lights unavailable but working from phone app: Tuya cloud auth token has expired. Check the config entries API for `tuya setup_error`. Fix by opening the integrations dashboard in the HA web UI, clicking Reconfigure on the Tuya entry, and scanning the QR code with the Smart Life or Tuya Smart phone app. This requires human interaction - the user must scan with their phone.

AC unavailable: IP likely changed on the LAN. Run `ha-ac-recover-ip`. The toggle script calls recovery automatically.

Web UI password lost: the auth provider storage file under HA's config directory contains bcrypt-hashed passwords. Generate a new bcrypt hash (needs the bcrypt Python package via nix-shell), write it to that file, restart the HA service, and update the password store.
</troubleshooting>

<traps>
The Midea integration needs the `midea-local` pip package inside the container. On image updates, pip packages are lost unless the config volume is mounted.

The REST API returns empty body for service calls (turn_on, set_temperature) - only state queries return JSON.
</traps>

<adding_devices>
New Tuya devices appear after pairing in the Smart Life app - HA picks them up on reload. If Tuya auth is expired, re-authenticate first. New Midea devices need auto-discovery through the config flow in HA. Both scripts follow identical patterns - read existing code before modifying.
</adding_devices>
