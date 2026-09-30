# GitHub — wz1119/Codex-Minecraft-Gameplay

Capture: `ReadItLater Inbox/GitHub - wz1119Codex-Minecraft-Gameplay A toolkit for exploring, gathering, crafting, and building in Minecraft with GPT-6 Astra computer use..md`
Origin: https://github.com/wz1119/Codex-Minecraft-Gameplay
Verdict: **reference**

## The origin as resolved

Opened the capture's GitHub repository directly and cloned it at
`7a41ebf3d1908512bc533e20fd378676853ddef2` (2026-09-07), rather than searching for the topic. The repository
is Apache-2.0 and has six commits, all from 2026-09-06 and 2026-09-07. Its substantive contents are one agent
skill, two reference pages, a Win32 input-and-screenshot adapter, a checked sequence runner, and mock/synthetic
tests. It names Wuyang Zhou and Tianyu Wei as copyright holders.

The advertised GPT-6 Astra is not part of the repository. The project contains no model, Minecraft client,
world, mod, or game-memory integration. It is a local computer-use layer intended to be opened as a Codex
project on the same Windows PC that is visibly running Minecraft.

## What it actually is

The useful part is not Minecraft knowledge so much as a bounded GUI-action protocol:

- `agents/skills/minecraft-gameplay/runtime/minecraft_control.py` finds a visible Minecraft process, focuses
  one exact window, injects physical scan-code keyboard and relative mouse events with Win32 `SendInput`, and
  stops on focus loss, F8, a stop file, or a changed window identity. Individual holds are capped at five
  seconds.
- `agents/skills/minecraft-gameplay/runtime/minecraft_sequence.py` validates a whole JSON plan before sending
  input, caps it at 32 steps and 30 seconds, requires a visual check before coordinate clicks and after the
  final action, rejects repeated aim changes, and requires a pixel-progress check for repeated actions.
  A watchdog releases held keys and buttons if the worker hangs.
- The image comparisons are deliberately narrow signals (`pixels`, `bright_text`, and `red_pixels`), not
  semantic vision. They can show that a watched region changed or remained stable; the skill correctly tells
  the agent not to confuse that with proving an inventory count or gameplay goal.

I installed its sole dependency, Pillow, into a temporary virtual environment and ran its upstream suite on
chise: 50 mock/synthetic tests passed in 1.160 seconds. That validates the platform-neutral plan validation,
watchdog, cleanup, and image-comparison logic. It does not validate live input: the adapter explicitly raises
`This adapter requires Windows` before constructing its Win32 backend.

## What it touches here

It touches no file now. It replaces and deletes nothing.

There is a real future fit on chise: `machine-configuration/machines/chise/home.nix:80` imports the Minecraft
module, and `machine-configuration/gaming/minecraft/minecraft-home-manager.nix:3` installs Prism Launcher.
But the repository exposes only an `x86_64-linux` NixOS host and two `aarch64-darwin` hosts at
`repository/flake-assembly/outputs.nix:3-29`; there is no Windows deployment target on which the captured
runtime could execute.

The nearest existing capability is
`agent-harness/agent-instructions/skills/workstation/desktop/SKILL.md:3-15`, which routes screenshots plus
Linux/Wayland keyboard and mouse control. It is not a substitute for the captured runtime:

- `agent-harness/agent-instructions/skills/workstation/desktop/references/keyboard.md:3-11` types text or a
  key/combo into whichever window is focused; it has no sustained key lease or per-action cleanup.
- `agent-harness/agent-instructions/skills/workstation/desktop/references/mouse.md:3-12` provides absolute
  clicks, moves, scrolling, and dragging; Minecraft camera control needs bounded relative motion and held
  buttons.
- `agent-harness/agent-instructions/skills/workstation/desktop/references/screenshot.md:3-11` can capture the
  active Hyprland window, but it does not bind later input to the same process/window identity.

A real adoption would therefore be a Linux port owned as a new workstation skill, not a copy of the captured
files: Hyprland window discovery and identity guards, relative mouse and held-key primitives, Pillow packaging,
the checked sequence runner, unit tests, and a live Prism Launcher/Minecraft verification. Copying the current
skill into the catalog would advertise a capability every configured host rejects; wrapping the generic
desktop scripts would omit the safety properties that make this project worth keeping.

## Reasoning

**Reference**, not adopt. The upstream code is coherent and unusually careful about input ownership, bounded
actions, state checks, and cleanup, but its only concrete backend is Win32. Porting it without a running game
to exercise would leave the highest-risk layer—the one that holds movement and mouse buttons against the live
desktop—proved only by mocks. That is merely workable evidence, not enough to expose the skill to agents.

Not a trial: there is no Windows host in the configuration, so the actual runtime cannot be trialled here.
Not a learn: there is no study or practice objective; the value is a concrete implementation to consult when
a Linux gameplay request justifies the port. Not a drop: chise already has Minecraft, and the checked-sequence
design is materially stronger than the generic desktop primitives, so the source has a specific retrieval use
rather than speculative novelty.

Cost now is one vault reference and one link in the existing AI Agent Skills MOC. It installs nothing, adds no
dependency, and makes no machine or agent capability claim.

## Drafted vault entry

Write `Second Brain/Inspiration/wz1119 - Codex Minecraft Gameplay.md` after approval, and add
`[[wz1119 - Codex Minecraft Gameplay]]` under `## Notes` in `Second Brain/Atlas/AI Agent Skills MOC.md`:

```markdown
---
title: "wz1119/Codex-Minecraft-Gameplay"
type: reference
status: filed
source-url: https://github.com/wz1119/Codex-Minecraft-Gameplay
creator: Wuyang Zhou and Tianyu Wei
platform: GitHub
captured: 2026-09-30
rating: worth-knowing
license: Apache-2.0
tags:
  - topic/ai-agents
---

Up: [[AI Agent Skills MOC]]

## What it is

An Apache-2.0 Codex skill plus Python runtime for controlling a visible Minecraft window through keyboard,
mouse, and screenshots. The backend is Windows-only and contains no model, game client, world, mod, or
memory API. Its durable contribution is a bounded action protocol: validate the whole plan before input,
cap actions and wall time, bind input to one foreground window, require visual checkpoints around menu
coordinates and the final state, demand progress evidence for repetition, and release held inputs through a
watchdog on failure.

## What to steal

- Treat input as a lease. Record ownership before a press can become uncertain, and make an independent
  watchdog release only the keys and buttons the action owns.
- Validate the complete batch before the first event. A bad later step must not discover itself after earlier
  movement or inventory changes have already happened.
- Require a confirmed layout before coordinate clicks and a checked end state after the final action.
- Put hard ceilings at every layer: five seconds per hold, 32 expanded steps, and 30 seconds per sequence.
- Call pixel checks what they are: stall and layout signals, not semantic proof of resources or completion.

## Fit here

Chise installs Prism Launcher, but this runtime calls Win32 `SendInput` and rejects non-Windows hosts. The
local desktop skill has screenshots and Linux/Wayland input, but lacks relative camera motion, held-input
leases, Minecraft window identity guards, and the checked sequence runner. Use this source when a concrete
request justifies a Linux/Hyprland port; do not install it verbatim or advertise it as a current capability.
```
