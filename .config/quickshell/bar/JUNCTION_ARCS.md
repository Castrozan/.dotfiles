# Junction Arc Geometry

Junction arcs are concave fillets connecting panel extensions to the bar strip. They appear in BarBackgroundShape.qml (fill) and BarInternalBorderShape.qml (stroke border), which must always trace identical paths.

## Anatomy of a Junction

Each junction is a PathLine followed by a PathArc. The PathLine positions the arc start point, and the PathArc defines the endpoint, radius, and sweep direction. Together they produce a 90-degree quarter-circle fillet in the concave corner between a strip edge and a panel edge.

## The Two Rules

**Rule 1 — Start offset points AWAY from the panel, toward the strip.** The PathLine Y (for vertical strip junctions) or X (for horizontal strip junctions) must offset from the panel edge in the direction of the approaching strip, not into the panel interior. A top junction on the right strip uses `panelTop - radius` (above the panel), placing the fillet in the empty space between strip and panel top. A bottom junction uses `panelBottom + radius` (below the panel). Getting this wrong rotates the fillet 90 degrees into the panel body.

**Rule 2 — Arc direction follows the bar's clockwise winding.** The bar perimeter is traced clockwise. Most junction arcs use `PathArc.Clockwise` because the concave fillet sits on the inside of a clockwise turn. The exception is the left extension bottom junction, which uses `PathArc.Counterclockwise` — at that point the path enters the extension rightward from the downward strip, and the clockwise winding places the concavity on the opposite side. When corner-merged, it switches to `PathArc.Clockwise` because the junction collapses into the strip corner. Panel corner arcs (convex rounded corners at the far edges of panels) always use `PathArc.Counterclockwise`.

## Horizontal Strip Panels (Dashboard, Launcher)

Panels hang from the inner edge of a horizontal strip. Dashboard hangs downward from the top strip; launcher hangs upward from the bottom strip. The path travels horizontally along the strip inner edge, enters the panel via a junction, traces the panel perimeter, and exits via another junction.

```
    strip inner edge ─────╮          ╭─────
                          │  panel   │
                          ╰──────────╯
```

Entry junction: PathLine to `(panelX - radius, stripY)`, arc to `(panelX, stripY + radius)`, CW.
Exit junction: PathLine to `(panelRight, stripY + radius)`, arc to `(panelRight + radius, stripY)`, CW.
Panel corners: both CCW.

## Vertical Strip Panels — Right Side (Session, Sidebar, Utilities, OSD)

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

## Vertical Strip Panels — Left Extension

The left extension hangs rightward from the left vertical strip inner edge. The path travels downward along the strip inner edge, enters the extension via the bottom junction, traces the extension perimeter clockwise, and exits via the top junction.

```
    strip │
          ╰────╮
          panel│
          ╭────╯
    strip │
```

Bottom junction: PathLine to `(stripRight, panelBottom + radius)`, arc to `(stripRight + radius, panelBottom)`, **CCW** (CW when corner-merged).
Top junction: PathLine to `(stripRight + radius, panelTop)`, arc to `(stripRight, panelTop - radius)`, CW.
Panel corners (top-right and bottom-right): both CCW.

The bottom junction is the only junction that uses CCW in its normal (non-merged) state. This happens because the path enters the extension moving rightward from the downward-traveling strip — the clockwise winding places the concave fillet on the opposite side compared to all other junctions.

## Radius Clamping

Junction and corner arc radii must not exceed half the panel width. Without clamping, a narrow panel (like OSD at 56px) would have junction radius (36px) + corner radius (36px) = 72px, exceeding the panel width and causing overlapping path segments. Both are clamped to `Math.min(junctionRadius, panelWidth / 2, ...)`.

## Corner Merging

When a panel extends close enough to the strip's own rounded corner (within `junctionRadius` distance), the junction arc and strip corner merge. This is a three-state transition:

**Normal** — panel edge is more than `junctionRadius` from the strip corner. Standard junction arc with full radius. The bar's inner corner radius remains intact.

**Partially merged** (`cornerMerged = true`) — panel edge + `junctionRadius` reaches the strip corner. The bar's inner corner radius collapses to 0 (corner disappears). The junction arc radius transitions to `mergedArcRadius` — the remaining gap between panel edge and strip boundary — which shrinks as the panel extends further. The left extension bottom junction flips from CCW to CW at this point.

**Fully merged** (`fullyMerged = true`) — panel edge reaches the strip boundary (`mergedArcRadius <= 0`). Junction arc radius = 0, the arc disappears entirely. The panel edge IS the strip boundary. For the left extension, `bottomEdgeTargetX` jumps to `extensionRight - cornerArcRadius`, so the bottom strip now starts at the popout's far-right edge.

Properties like `topCornerMerged` / `rightPanelTopFullyMerged` control this transition. Merged corners hide arc direction bugs because a zero-radius arc is invisible regardless of direction.

The right panel aggregate (sidebar/notifications, session, utilities, OSD) is typically fully merged on both top and bottom. The sidebar spans from `stripThickness` to `screenHeight - stripThickness - utilitiesHeight`, and utilities fills the remaining gap to `screenHeight - stripThickness`. The aggregate bounding box covers the entire strip height, so both `rightPanelMergedTopArcRadius` and `rightPanelMergedBottomArcRadius` are 0.

## Aggregate Right Panel Geometry

Multiple right-side panels (session, sidebar, utilities, OSD) are combined into a single aggregate shape in Drawers.qml via `aggregatedRightPanelGeometry`. The aggregate Y, bottom, and width are computed as the bounding box of all visible right panels. BarBackgroundShape and BarInternalBorderShape receive this aggregate as a single `rightPanel` with one top junction and one bottom junction.
