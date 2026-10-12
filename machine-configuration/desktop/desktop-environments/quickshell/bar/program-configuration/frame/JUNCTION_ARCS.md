# Junction Arc Geometry

Junction arcs are concave fillets connecting panel extensions to an attachment edge. Fill and border share the exposed contour. The fill closes across the attachment edge; the stroke stays open so the window border joins the curved panel outline. BarFrameGeometry.qml computes the shared geometry.

Use one Shape with separate positive ShapePaths for each panel. Opaque panel fill covers the native window border at the attachment edge. The left bar has a closed fill path and a separate open border using the same popout contour. A desktop-sized outer rectangle minus a cutout puts coincident segments on the screen edge when the strip thickness is zero; the curve renderer can then fill the desktop instead of the panels.

## Anatomy of a Junction

Each junction is a PathLine followed by a PathArc. The PathLine positions the arc start point, and the PathArc defines the endpoint, radius, and sweep direction. Together they produce a 90-degree quarter-circle fillet in the concave corner between a strip edge and a panel edge.

## The Two Rules

**Rule 1 — Start offset points AWAY from the panel, toward the strip.** The PathLine Y (for vertical strip junctions) or X (for horizontal strip junctions) must offset from the panel edge in the direction of the approaching strip, not into the panel interior. A top junction on the right strip uses `panelTop - radius` (above the panel), placing the fillet in the empty space between strip and panel top. A bottom junction uses `panelBottom + radius` (below the panel). Getting this wrong rotates the fillet 90 degrees into the panel body.

**Rule 2: Arc direction follows the local contour.** Junction arcs use `PathArc.Clockwise`; convex panel corner arcs use `PathArc.Counterclockwise`. The left extension contour approaches its bottom junction while moving upward along the bar edge, so that junction also uses `PathArc.Clockwise`.

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

Bottom junction: PathLine to `(stripRight, panelBottom + radius)`, arc to `(stripRight + radius, panelBottom)`, **CW**.
Top junction: PathLine to `(stripRight + radius, panelTop)`, arc to `(stripRight, panelTop - radius)`, CW.
Panel corners (top-right and bottom-right): both CCW.

Both junctions use CW. The path approaches going upward along the bar edge and turns right into the extension — the same right-turn geometry as the top junction (left-to-down), so the same CW direction produces the concave fillet.

## Radius Clamping

Junction and corner arc radii must not exceed half the panel width. Without clamping, a narrow panel (like OSD at 56px) would have junction radius (36px) + corner radius (36px) = 72px, exceeding the panel width and causing overlapping path segments. Both are clamped to `Math.min(junctionRadius, panelWidth / 2, ...)`.

## Corner Merging

When a panel extends close enough to the strip's own rounded corner (within `junctionRadius` distance), the junction arc and strip corner merge. This is a three-state transition:

**Normal** — panel edge is more than `junctionRadius` from the strip corner. Standard junction arc with full radius. The bar's inner corner radius remains intact.

**Partially merged** (`cornerMerged = true`) — panel edge + `junctionRadius` reaches the strip corner. The bar's inner corner radius collapses to 0 (corner disappears). The junction arc radius transitions to `mergedArcRadius` — the remaining gap between panel edge and strip boundary — which shrinks as the panel extends further.

**Fully merged** (`fullyMerged = true`) — panel edge reaches the strip boundary (`mergedArcRadius <= 0`). Junction arc radius = 0, the arc disappears entirely. The panel edge IS the strip boundary. For the left extension, `bottomEdgeTargetX` jumps to `extensionRight - cornerArcRadius`, so the bottom strip now starts at the popout's far-right edge.

Properties like `topCornerMerged` / `rightPanelTopFullyMerged` control this transition. Merged corners hide arc direction bugs because a zero-radius arc is invisible regardless of direction.

The right panel aggregate is fully merged when its bounding box reaches both screen edges. Both `rightPanelMergedTopArcRadius` and `rightPanelMergedBottomArcRadius` are then 0.

## Aggregate Right Panel Geometry

Right-side panels share an aggregate contour whose bounds are computed in drawers/RightPanelGeometry.qml. Its bounding box determines the top and bottom junctions; the fill and stroke use the same path.
