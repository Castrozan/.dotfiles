# Dell G15 5515 Hardware Control Reference

Model: Dell G15 5515 (AMD, product_name from DMI)
BIOS: 1.28.1
Kernel: 6.1.159
ACPI path: `\_SB.AMW3.WMAX`

## Prerequisites

```bash
sudo modprobe acpi_call
```

## Power / Fan Control

### Power Modes (0x15 set, 0x14 get)

Only two modes work on G15 5515 (confirmed via Dell-G-Series-Controller patch.py):

```bash
# Set Manual mode
echo "\_SB.AMW3.WMAX 0 0x15 {0x01, 0x00, 0x00, 0x00}" > /proc/acpi/call

# Set G Mode (performance - fans go full speed, DO NOT use casually)
echo "\_SB.AMW3.WMAX 0 0x15 {0x01, 0xab, 0x00, 0x00}" > /proc/acpi/call

# Query current power mode
echo "\_SB.AMW3.WMAX 0 0x14 {0x0b, 0x00, 0x00, 0x00}" > /proc/acpi/call
cat /proc/acpi/call  # 0x0 = Manual, 0xab = G Mode
```

WARNING: 0xab is G Mode / thermal performance. It spins fans to maximum.
Other modes (0xa0 balanced, 0xa3 quiet, etc.) return 0xffffffff on this model.

### G Mode Toggle

```bash
# Toggle G Mode on/off
echo "\_SB.AMW3.WMAX 0 0x25 {0x01, 0x00, 0x00, 0x00}" > /proc/acpi/call

# Query G Mode status
echo "\_SB.AMW3.WMAX 0 0x25 {0x02, 0x00, 0x00, 0x00}" > /proc/acpi/call
cat /proc/acpi/call  # 0x0 = off, 0x1 = on
```

### Fan Boost

```bash
# Set CPU fan boost (0x32 = fan1 id, last arg = boost 0x00-0xFF)
echo "\_SB.AMW3.WMAX 0 0x15 {0x02, 0x32, BOOST, 0x00}" > /proc/acpi/call

# Set GPU fan boost (0x33 = fan2 id)
echo "\_SB.AMW3.WMAX 0 0x15 {0x02, 0x33, BOOST, 0x00}" > /proc/acpi/call

# Query CPU fan RPM
echo "\_SB.AMW3.WMAX 0 0x14 {0x05, 0x32, 0x00, 0x00}" > /proc/acpi/call

# Query GPU fan RPM
echo "\_SB.AMW3.WMAX 0 0x14 {0x05, 0x33, 0x00, 0x00}" > /proc/acpi/call

# Query CPU temp
echo "\_SB.AMW3.WMAX 0 0x14 {0x04, 0x01, 0x00, 0x00}" > /proc/acpi/call

# Query GPU temp
echo "\_SB.AMW3.WMAX 0 0x14 {0x04, 0x06, 0x00, 0x00}" > /proc/acpi/call
```

## Keyboard LED Controller

USB device: `187c:0550` — Alienware LED controller
Firmware: 1.1.7
Platform type: 0x0e05
Zones: 16
Power state animations: 7+ (firmware-protected, cannot be fully removed)

### What Works

**Dimming via USB HID** — the ONLY reliable method found.

Requirements:
1. `alienware-wmi` kernel module must be UNLOADED (`rmmod alienware_wmi`)
2. Must cycle `modprobe alienware_wmi && rmmod alienware_wmi` before sending commands
3. Use the DIMMING command (0x26) with zone list
4. Dimming scale is 0-100, INVERTED: 0 = full bright, 100 = fully off

The dimming command dims whatever color the firmware animations are showing (cyan by default).
No flicker. Persists until driver is reloaded or reboot.

### What Does NOT Work

| Method | Result |
|--------|--------|
| `alienware-wmi` sysfs (`global_brightness`, `rgb_zones`) | Writes accepted, no hardware effect |
| USB HID `SET_COLOR` (0x27) | Command accepted, no visible effect |
| USB HID `finish_save` (0x02) animations | Corrupts firmware state, reverts to cyan 100% |
| USB HID `finish_play` (0x03) animations | Changes color but causes flickering |
| ACPI `\_SB.AMW3.WMAX 0x14/0x15` | These are thermal/power modes, not keyboard |
| EC register writes | No keyboard backlight register found |
| Fn keyboard backlight key | No effect (EC dump shows no register change) |
| `brightnessctl` / `openrgb` | No keyboard device detected |
| sysfs `alienware::global_brightness` | Reads/writes but does not control hardware |

### Protocol Details (USB HID)

Report length: 33 bytes. Prefix: 0x03.

```
SET_REPORT: bmRequestType=0x21, bRequest=0x09, wValue=0x0200, wIndex=0x00
GET_REPORT: bmRequestType=0xA1, bRequest=0x01, wValue=0x0100, wIndex=0x00
```

Command format: `03 CMD [args...] [zero-padded to 33 bytes]`

Key commands:
- `20 XX` — ELC_QUERY (00=version, 02=platform/zones, 03=animation count)
- `21 SUBCMD ANIM_ID` — USER_ANIMATION
- `22 SUBCMD ANIM_ID` — POWER_ANIMATION
- `23 LOOP ZONE_COUNT ZONES...` — START_SERIES
- `24 EFFECT DUR(2) TEMPO(2) R G B` — ADD_ACTION
- `26 DIM_VALUE ZONE_COUNT ZONES...` — DIMMING (0=bright, 100=off)
- `27 R G B ZONE_COUNT ZONES...` — SET_COLOR

Animation sub-commands: 01=START_NEW, 02=FINISH_SAVE, 03=FINISH_PLAY, 04=REMOVE, 05=PLAY, 06=SET_DEFAULT

Power state animation IDs: 0x5b=AC_SLEEP, 0x5c=AC_CHARGED, 0x5d=AC_CHARGING, 0x5e=DC_SLEEP, 0x5f=DC_ON, 0x60=DC_LOW, 0x61=DEFAULT_POST_BOOT

### References

- [Dell-G-Series-Controller](https://github.com/cemkaya-mpi/Dell-G-Series-Controller) — PyQt GUI, USB HID protocol
- [Dell-G-Series-Controller-awcc-fix](https://github.com/PatrickMeerssche/Dell-G-Series-Controller-awcc-fix) — AWCC hotfix fork
- [ArchWiki Dell G15 5515](https://wiki.archlinux.org/title/Dell_G15_5515) — ACPI commands
- [ArchWiki Dell G15 5525](https://wiki.archlinux.org/title/Dell_G15_5525) — Related model
