# Junction Arc Geometry

Junction arcs are concave fillets connecting panel extensions to the bar strip. They appear in BarBackgroundShape.qml (fill) and BarInternalBorderShape.qml (stroke border), which must always trace identical paths.

## Anatomy of a Junction

Each junction is a PathLine followed by a PathArc. The PathLine positions the arc start point, and the PathArc defines the endpoint, radius, and sweep direction. Together they produce a 90-degree quarter-circle fillet in the concave corner between a strip edge and a panel edge.

## The Two Rules

**Rule 1 — Start offset points AWAY from the panel, toward the strip.** The PathLine Y (for vertical strip junctions) or X (for horizontal strip junctions) must offset from the panel edge in the direction of the approaching strip, not into the panel interior. A top junction on the right strip uses `panelTop - radius` (above the panel), placing the fillet in the empty space between strip and panel top. A bottom junction uses `panelBottom + radius` (below the panel). Getting this wrong rotates the fillet 90 degrees into the panel body.

**Rule 2 — Arc direction is always Clockwise.** All junction arcs in the bar use `PathArc.Clockwise`. This holds for both left-side panels (dashboard, launcher hanging from horizontal strips) and right-side panels (session, sidebar, utilities, OSD hanging from the vertical strip). Panel corner arcs (the convex rounded corners at the far edges of panels) use `PathArc.Counterclockwise`.

## Horizontal Strip Panels (Dashboard, Launcher)

Panels hang downward from the top or bottom horizontal strip edge. The path travels horizontally along the strip inner edge, enters the panel via a junction, traces the panel perimeter, and exits via another junction.

```
    strip inner edge ──────────────────
                  ╭──────────╮
                  │  panel   │
                  ╰──────────╯
```

Entry junction: PathLine to `(panelX - radius, stripY)`, arc to `(panelX, stripY + radius)`, CW.
Exit junction: PathLine to `(panelRight, stripY + radius)`, arc to `(panelRight + radius, stripY)`, CW.
Panel corners: both CCW.

## Vertical Strip Panels (Session, Sidebar, Utilities, OSD)

Panels hang leftward from the right vertical strip edge. The path travels downward along the strip inner edge, enters the panel via the top junction, traces the panel perimeter, and exits via the bottom junction.

```
         │ strip
    ╭────╯
    │ panel
    ╰────╮
         │ strip
```

Top junction: PathLine to `(stripX, panelTop - radius)`, arc to `(stripX - radius, panelTop)`, CW.
Bottom junction: PathLine to `(stripX - radius, panelBottom)`, arc to `(stripX, panelBottom + radius)`, CW.
Panel corners (top-left and bottom-left): both CCW.

## Radius Clamping

Junction and corner arc radii must not exceed half the panel width. Without clamping, a narrow panel (like OSD at 56px) would have junction radius (36px) + corner radius (36px) = 72px, exceeding the panel width and causing overlapping path segments. Both are clamped to `Math.min(junctionRadius, panelWidth / 2, ...)`.

## Corner Merging

When a panel extends close enough to the strip's own rounded corner (within `junctionRadius` distance), the junction arc and strip corner merge. The junction radius collapses toward zero and the panel edge clamps to the strip boundary. Properties like `topCornerMerged` and `rightPanelTopFullyMerged` control this transition. Merged corners hide arc direction bugs because a zero-radius arc is invisible regardless of direction.

## Aggregate Right Panel Geometry

Multiple right-side panels (session, sidebar, utilities, OSD) are combined into a single aggregate shape in Drawers.qml via `aggregatedRightPanelGeometry`. The aggregate Y, bottom, and width are computed as the bounding box of all visible right panels. BarBackgroundShape and BarInternalBorderShape receive this aggregate as a single `rightPanel` with one top junction and one bottom junction.
