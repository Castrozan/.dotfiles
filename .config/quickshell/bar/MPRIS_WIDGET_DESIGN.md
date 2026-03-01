# Bar Extension Popout System + MPRIS Widget

Redesign popouts so the bar physically extends outward as one continuous shape when hovering icons. Reference: caelestia-shell's `modules/bar/popouts/Background.qml` and `modules/drawers/Backgrounds.qml`.

## Core Architecture

A single QML `Shape` element draws the bar background + any active popout extension as one continuous filled path. No separate floating windows.

```
  Normal bar          With extension active

  ╭────╮              ╭────╮
  │    │              │    │
  │    │              │    ╰──────────────────╮
  │    │              │     extension content │
  │    │              │    ╭──────────────────╯
  │    │              │    │
  ╰────╯              ╰────╯
```

One `ShapePath` draws the full outline — left side runs the full bar height, right side has a notch that curves outward at the extension zone. All corners are rounded.

## Shape Path Geometry

The path traces clockwise from top-left:

```
  A╭────╮B
   │    │
   │    │C
   │    ╰──────╮D
   │           │
   │           │
   │    ╭──────╯E
   │    │F
   │    │
  H╰────╯G

  Path order: A → B → C → D → E → F → G → H → A

  A: top-left arc
  B: top-right arc
  C: straight down to extension top
  C→D: arc curving right (extension top-right corner)
  D: straight right along extension top
  D→corner: arc (extension far top-right)
  down: straight along extension right side
  corner→E: arc (extension far bottom-right)
  E: straight left along extension bottom
  E→F: arc curving left back to bar (extension bottom-left)
  F: straight down to bottom
  G: bottom-right arc
  H: bottom-left arc
  back to A
```

When no extension is active, the path simplifies to a plain rounded rectangle (C=B, F=G — no notch).

## Caelestia Reference

Key files to study in `~/repo/caelestia-shell/`:

- `modules/bar/popouts/Background.qml` — ShapePath that draws the popout shape with dynamic arcs based on wrapper position
- `modules/drawers/Backgrounds.qml` — master Shape element, uses `Shape.CurveRenderer`, anchors fill parent
- `modules/drawers/Panels.qml` — positions popout Wrapper at `x: 0` so it aligns with bar edge
- `modules/bar/popouts/Wrapper.qml` — popout container with `currentCenter` binding for Y positioning

Pattern: one centralized `Shape` renders all backgrounds. Each popout type is a `ShapePath` child. The shape uses `preferredRendererType: Shape.CurveRenderer` for smooth beziers.

## MPRIS Extension Content

When hovering the media icon, the bar extends:

```
  ╭────╮
  │    │
  │    ╰──────────────────────────────────╮
  │ 󰎆   ▶  Song Title – Artist            │
  │      feishin          ◄◄  ❚❚  ►►      │
  │    ╭──────────────────────────────────╯
  │    │
  ╰────╯
```

- Line 1: playback state icon + "Title – Artist"
- Line 2: player name (dim) + transport controls

Data: `playerctl` polled every 2s. Controls: `playerctl play-pause/next/previous`.

## Implementation Plan

### Phase 1: Replace popout background with Shape-based bar extension

Replace the current `Rectangle` bar background + separate `PopoutWrapper` with a unified `Shape` that draws bar + extension as one path.

Files to modify:
- `bar/BarWrapper.qml` — replace Rectangle background with Shape
- `bar/Drawers.qml` — embed extension content inside the shape area instead of a separate layershell region

New files:
- `bar/BarBackgroundShape.qml` — ShapePath component that draws the unified outline

### Phase 2: Add MPRIS popout content

New files:
- `bar/popouts/MprisPopout.qml` — media player extension content

Modified files:
- `bar/modules/StatusIconsModule.qml` — add MPRIS icon
- `bar/popouts/PopoutContent.qml` — add "mpris" route
- `bar/popouts/qmldir` — register MprisPopout
