# NixOS Flake Configuration Review - Implementation Plan

## Overview

This document outlines the implementation plan for improving the NixOS flake configuration based on the comprehensive review.

## Implementation Phases

### Phase 1: Critical Fixes (Immediate)

1. **Remove keyd.nix module**
   - Delete `nixos/modules/keyd.nix`
   - Remove import from `users/zanoni/nixos.nix:18`

2. **Remove or use flake-utils**
   - Currently declared but unused in `flake.nix:16`
   - Remove if not needed, or implement multi-system support

3. **Add inline comments to flake.nix**
   - Explain why some flakes use tags vs revs
   - Document that castrozan repos have full control
   - Note code-first update approach (change code directly, not manual commands)

### Phase 2: Store Optimization (This Week)

1. **Add automatic store optimization**
   - Add `nix.optimise.automatic = true` to `hosts/dellg15/configs/configuration.nix`
   - Set appropriate schedule (e.g., daily at 3:45 AM)
   - Test manual optimization: `sudo nix-store --optimise`
   - Monitor disk space savings

### Phase 4: Code Quality (This Month)

1. **Consolidate allowUnfree declarations**
   - Remove redundant declarations from `flake.nix:53,57,61`
   - Keep system-level in `configuration.nix:73`
   - Keep module-specific predicate in `steam.nix:11`

2. **Review virtualization.nix**
   - Resolve TODOs about Docker/libvirt configuration
   - Verify it's not breaking the system
   - Document findings

3. **Review NIX_PATH configuration**
   - Review commented-out NIX_PATH options in `users/zanoni/nixos.nix:47-52`
   - Determine best approach and document

## Completed Items

- ✅ Cursor.nix version handling - confirmed intentional (using pkgs for appimageTools is correct)
- ✅ nixos-init - decided not to use

## Notes

- **Update Strategy**: Code-first approach - update flake.nix directly when updates are needed, not via manual commands
- **Own Repos**: Most external flakes are castrozan repos with full control, allowing flexible update strategies
- **Tag vs Rev**: 
  - Tags used for stable releases (zed-editor, opencode, tui-notifier, readItNow-rc)
  - Rev/commit used for specific pinned versions or when flake parsing is disabled (whisper-input)
  - Branch/default used for actively maintained repos (cbonsai, cmatrix, tuisvn, install-nothing)

## Status

- [x] Phase 1: Critical Fixes
- [x] Phase 2: Store Optimization  
- [x] Phase 4: Code Quality
