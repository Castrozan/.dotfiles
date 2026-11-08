import json
import pathlib
import subprocess

AMBIENT_CANVAS_WEB_DIRECTORY = pathlib.Path(__file__).resolve().parents[3] / "web"
TOKEN_FIELD_DIRECTORY = AMBIENT_CANVAS_WEB_DIRECTORY / "scenes" / "token-field"
SCENE_SCRIPT_PATHS = [
    AMBIENT_CANVAS_WEB_DIRECTORY / "ambient_canvas_palette.js",
    TOKEN_FIELD_DIRECTORY / "token_field_vocabulary.js",
    TOKEN_FIELD_DIRECTORY / "token_field_timeline.js",
    TOKEN_FIELD_DIRECTORY / "token_field_layout.js",
    TOKEN_FIELD_DIRECTORY / "token_field_glyph_atlas.js",
    TOKEN_FIELD_DIRECTORY / "token_field_scene.js",
]
NODE_EVALUATION_TIMEOUT_SECONDS = 60
BROWSER_STUB = """
global.window = global;
global.location = { search: "" };
const recordingContext = (operations) => ({
  measureText: () => ({ width: 11.2 }),
  fillText() {},
  fillRect() {},
  drawImage(...drawArguments) {
    operations.push([this.globalAlpha, ...drawArguments.slice(1)]);
  },
});
global.document = {
  documentElement: { style: { setProperty() {} } },
  createElement: () => ({ getContext: () => recordingContext([]) }),
};
const loadScenes = (paths) => {
  for (const path of paths) {
    (0, eval)(require("node:fs").readFileSync(path, "utf8"));
  }
};
const createRenderer = (width, height, startSeconds) => {
  const operations = [];
  const canvas = { width, height, getContext: () => recordingContext(operations) };
  const renderer = window.AMBIENT_CANVAS_SCENE_FACTORIES["token-field"](
    canvas,
    { startSeconds },
  );
  return {
    renderer,
    frameAt(seconds) {
      operations.length = 0;
      renderer.render(seconds);
      return JSON.stringify(operations);
    },
  };
};
"""


def evaluate_in_node(body):
    script_paths = json.dumps([str(path) for path in SCENE_SCRIPT_PATHS])
    program = f"{BROWSER_STUB}\nloadScenes({script_paths});\n{body}"
    completed = subprocess.run(
        ["node", "-e", program],
        check=True,
        capture_output=True,
        text=True,
        timeout=NODE_EVALUATION_TIMEOUT_SECONDS,
    )
    return json.loads(completed.stdout)
