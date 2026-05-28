# AeroSpace on macOS 26 Tahoe

## Why aerospace.nix uses a custom Castrozan fork

macOS 26 (Tahoe) added a strict `anchor apple` platform-requirement check to TCC's accessibility path. AeroSpace upstream is self-signed with an `aerospace-codesign-certificate` (no Apple Developer ID), so this check fails on every TCC query - even after the user grants accessibility. `tccd` returns `Auth Right: Allowed (System Set)` but also `matches platform requirements: No` and `promptType: 1`.

Upstream's `checkAccessibilityPermissions` ran `tccutil reset Accessibility bobko.aerospace` followed by `terminateApp()` whenever `AXIsProcessTrustedWithOptions` returned false. On Tahoe that's every launch, and combined with launchd `KeepAlive` it produced an infinite respawn + prompt loop.

The fork at `github:Castrozan/AeroSpace/fix/tahoe-ax-prompt-loop` drops the reset + terminate branch. AeroSpace stays alive when the trust check fails; actual `AXUIElementCopyAttributeValue` calls still work because TCC's stored `auth_right` is `Allowed`.

## The lingering popup (`universalAccessAuthWarn`)

AeroSpace's startup `AXIsProcessTrustedWithOptions(prompt: true)` call still fires the system accessibility dialog on first launch because the platform-check returns false. macOS spawns `universalAccessAuthWarn` (in `/System/Library/PrivateFrameworks/UniversalAccess.framework/`) to render the dialog. Once on screen the dialog does not auto-dismiss when the user toggles accessibility on: it re-queries `tccd`, sees `promptType: 1` again, and stays.

This is **not** an AeroSpace bug. It happens to any ad-hoc-signed AX app on Tahoe, and per [BetterTouchTool forum](https://community.folivora.ai/t/accessibility-api-permissions-window-still-pops-up/45119) it also affects properly developer-signed apps (Apple calls it permission-database corruption).

## Workaround when the popup gets stuck

```fish
killall universalAccessAuthWarn
```

The daemon does not auto-respawn. AeroSpace keeps working. Re-fire only if AeroSpace itself restarts (rare - launchd doesn't kill it anymore).

## Real fix path

Signing the binary with a real Apple Developer ID (`Developer ID Application: ...`) satisfies `anchor apple` and removes the popup permanently. Requires Apple Developer Program membership ($99/yr). Until then the workaround above is the answer.

## Things that do NOT fix this

- `tccutil reset Accessibility bobko.aerospace` - tested, popup returns
- `sudo tccutil reset All bobko.aerospace` - tested, popup returns
- Reinstalling via brew cask, downgrading to 0.19.x, using HM-installed nix .app - all tested, all bombard the same way on Tahoe
- macOS minor upgrades (26.0 → 26.1+) - none have relaxed the platform-check
