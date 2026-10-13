# Junction Arc Geometry

Junction arcs are concave fillets connecting panel extensions to an attachment edge. Fill and border share the exposed contour. The fill closes across the attachment edge; the stroke stays open so the window border joins the curved panel outline. BarFrameGeometry.qml computes the shared geometry.

Use one Shape with separate positive ShapePaths for each panel. Opaque panel fill covers the native window border at the attachment edge. The left bar and right panels use open borders over their filled contours. Border paths skip segments along screen edges covered by a panel. A desktop-sized outer rectangle minus a cutout puts coincident segments on the screen edge when the strip thickness is zero; the curve renderer can then fill the desktop instead of the panels.

The stroke center is inset by half the window border width into the remaining window. This aligns its two pixels with the native border and prevents a straight native border segment from crossing a curve endpoint. Fill closures still reach the physical screen edges. Dashboard and launcher attachment covers use Qt's PathRectangle with no stroke; they do not reserve space or paint a permanent desktop frame.

## Anatomy of a Junction

Each junction is a PathLine followed by a PathArc. The PathLine positions the arc start point, and the PathArc defines the endpoint, radius, and sweep direction. Together they produce a 90-degree quarter-circle fillet in the concave corner between a strip edge and a panel edge.

## The Two Rules

**Rule 1 — Start offset points AWAY from the panel, toward the strip.** The PathLine Y (for vertical strip junctions) or X (for horizontal strip junctions) must offset from the panel edge in the direction of the approaching strip, not into the panel interior. A top junction on the right strip uses `panelTop - radius` (above the panel), placing the fillet in the empty space between strip and panel top. A bottom junction uses `panelBottom + radius` (below the panel). Getting this wrong rotates the fillet 90 degrees into the panel body.

**Rule 2: Arc direction follows the local contour.** Junction arcs use `PathArc.Clockwise`; convex panel corner arcs use `PathArc.Counterclockwise`. When a panel reaches a screen edge, its corner becomes a rounded corner of the remaining window and uses `PathArc.Clockwise`. The left extension contour approaches its bottom junction while moving upward along the bar edge, so that junction also uses `PathArc.Clockwise`.

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
Panel corners (top-left and bottom-left): CCW until the panel reaches the screen edge, then CW.

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
Panel corners (top-right and bottom-right): CCW until the popout reaches the screen edge, then CW.

Both junctions use CW. The path approaches going upward along the bar edge and turns right into the extension — the same right-turn geometry as the top junction (left-to-down), so the same CW direction produces the concave fillet.

## Radius Clamping

Adjacent arcs must fit their available contour span. Right-side junction and corner radii are each capped at half the panel width, preventing overlap when the width is below twice `junctionRadius`. Top and bottom panel corners use the span between border centers; their junction radii also leave room for the corner arcs.

## Corner Merging

When a panel extends close enough to the strip's own rounded corner (within `junctionRadius` distance), the junction arc and strip corner merge. This is a three-state transition:

**Normal** — panel edge is more than `junctionRadius` from the strip corner. Standard junction arc with full radius. The bar's inner corner radius remains intact.

**Partially merged** (`cornerMerged = true`): the panel approaches the screen edge. For a left popout, the available gap bounds both the bar corner and junction radii so their tangents meet without a square corner. The right-side junction uses the remaining gap to the screen edge.

**Fully merged** (`fullyMerged = true`): the panel reaches the native border (`mergedArcRadius <= 0`). The junction arc disappears and the remaining window corner rounds toward the panel. The border omits the covered screen-edge segment. For the left extension, `bottomEdgeTargetX` becomes `extensionBorderRightEdge + cornerArcRadius`, where the window's bottom edge meets the rounded corner.

The left bar retains rounded window corners while visible even when strip thickness is zero. Its corner radius is clamped to its animated width and the junction radius; hiding it collapses those corners without painting a permanent frame.

Properties like `topCornerMerged` / `rightPanelTopFullyMerged` control this transition. Merged corners hide arc direction bugs because a zero-radius arc is invisible regardless of direction.

The right panel aggregate is fully merged when its bounding box reaches both native border bands. Both `rightPanelMergedTopArcRadius` and `rightPanelMergedBottomArcRadius` are then 0.

## Aggregate Right Panel Geometry

Right-side panels share an aggregate contour whose bounds are computed in drawers/RightPanelGeometry.qml. Its bounding box determines the top and bottom junctions; the fill and stroke share the exposed contour.
