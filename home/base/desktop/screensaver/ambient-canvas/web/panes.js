window.AMBIENT_CANVAS_ROTATION_SECONDS = 20;

window.AMBIENT_CANVAS_PLAYLIST = [
  { panes: [{ scene: "yuruyurau", options: { variant: "twin" } }] },
  { panes: [{ scene: "yuruyurau", options: { variant: "solo" } }] },
  { panes: [{ scene: "yuruyurau", options: { variant: "swirl" } }] },
  { panes: [{ scene: "yuruyurau", options: { variant: "petal" } }] },
  { panes: [{ scene: "bonsai" }] },
  { panes: [{ scene: "matrix" }] },
  {
    durationSeconds: 30,
    layout: {
      columnTemplate: "2fr 1fr",
      rowTemplate: "1fr 1fr",
      areaRows: ["yuruyurau bonsai", "yuruyurau matrix"],
    },
    panes: [
      { area: "yuruyurau", scene: "yuruyurau", options: { variant: "twin" } },
      { area: "bonsai", scene: "bonsai" },
      { area: "matrix", scene: "matrix" },
    ],
  },
];
