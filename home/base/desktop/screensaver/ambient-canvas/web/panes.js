window.AMBIENT_CANVAS_ROTATION_SECONDS = 20;

window.AMBIENT_CANVAS_PLAYLIST = [
  { panes: [{ scene: "yuruyurau", options: { variant: "twin" } }] },
  { panes: [{ scene: "yuruyurau", options: { variant: "solo" } }] },
  { panes: [{ scene: "yuruyurau", options: { variant: "swirl" } }] },
  { panes: [{ scene: "yuruyurau", options: { variant: "petal" } }] },
  { panes: [{ scene: "bonsai" }] },
  { panes: [{ scene: "matrix" }] },
  {
    panes: [
      {
        scene: "bad-apple",
        options: { videoId: "FtutLA63Cp8", startSeconds: 30 },
      },
    ],
  },
  {
    panes: [
      {
        scene: "bad-apple",
        options: { videoId: "CqaAs_3azSs", startSeconds: 45 },
      },
    ],
  },
  {
    panes: [
      {
        scene: "bad-apple",
        options: { videoId: "lX44CAz-JhU", startSeconds: 40 },
      },
    ],
  },
  {
    panes: [
      {
        scene: "bad-apple",
        options: { videoId: "djV11Xbc914", startSeconds: 50 },
      },
    ],
  },
  {
    panes: [
      {
        scene: "bad-apple",
        options: { videoId: "OBk3ynRbtsw", startSeconds: 25 },
      },
    ],
  },
  {
    panes: [
      {
        scene: "bad-apple",
        options: {
          videoId: "I03xFqbxUp8",
          startSeconds: 60,
          luminanceThreshold: 0.12,
        },
      },
    ],
  },
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
