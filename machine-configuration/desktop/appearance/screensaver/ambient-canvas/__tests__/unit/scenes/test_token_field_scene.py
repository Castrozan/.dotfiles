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
CAPTURE_FRAMES_PER_SECOND = 60
RECORDED_CHUNK_SECONDS = 30
LARGEST_ALPHA_CHANGE_PER_FRAME = 0.012
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
        ["node", "-e", program], check=True, capture_output=True, text=True
    )
    return json.loads(completed.stdout)


def sweep_envelopes():
    return evaluate_in_node(
        f"""
        const timeline = window.AmbientCanvasTokenFieldTimeline;
        const envelope = new Float32Array(4);
        const orderSteps = 20;
        let openingMismatch = 0;
        let closingMismatch = 0;
        let largestChange = 0;
        const frameSeconds = 1 / {CAPTURE_FRAMES_PER_SECOND};
        const generationSeconds = timeline.cycleDurationSeconds / timeline.GENERATION_COUNT;
        const phaseStep = frameSeconds / generationSeconds;
        for (let outgoingStep = 0; outgoingStep <= orderSteps; outgoingStep += 1) {{
          for (let incomingStep = 0; incomingStep <= orderSteps; incomingStep += 1) {{
            const outgoingOrder = outgoingStep / orderSteps;
            const incomingOrder = incomingStep / orderSteps;
            timeline.writeCellEnvelope(envelope, 0, outgoingOrder, incomingOrder);
            openingMismatch = Math.max(openingMismatch, Math.abs(envelope[0] - 1), envelope[1], envelope[2], envelope[3]);
            timeline.writeCellEnvelope(envelope, 1, outgoingOrder, incomingOrder);
            closingMismatch = Math.max(closingMismatch, envelope[0], envelope[1], envelope[2], Math.abs(envelope[3] - 1));
            let previous = null;
            for (let phase = 0; phase <= 1; phase += phaseStep) {{
              timeline.writeCellEnvelope(envelope, phase, outgoingOrder, incomingOrder);
              if (previous) {{
                for (let index = 0; index < 4; index += 1) {{
                  largestChange = Math.max(largestChange, Math.abs(envelope[index] - previous[index]));
                }}
              }}
              previous = Array.from(envelope);
            }}
          }}
        }}
        process.stdout.write(JSON.stringify({{ openingMismatch, closingMismatch, largestChange }}));
        """
    )


def test_every_cell_starts_as_its_word_and_ends_as_the_next_generation_word():
    sweep = sweep_envelopes()
    assert sweep["openingMismatch"] == 0
    assert sweep["closingMismatch"] == 0


def test_no_cell_changes_opacity_faster_than_the_smoothness_bound():
    assert sweep_envelopes()["largestChange"] < LARGEST_ALPHA_CHANGE_PER_FRAME


def test_the_last_generation_hands_back_to_the_first():
    moments = evaluate_in_node(
        """
        const timeline = window.AmbientCanvasTokenFieldTimeline;
        process.stdout.write(JSON.stringify(
          timeline.resolveGenerationMoment(timeline.cycleDurationSeconds - 0.001),
        ));
        """
    )
    assert moments["incomingGenerationIndex"] == 0
    assert moments["phase"] > 0.99


def test_the_last_recorded_frame_draws_exactly_the_first_frame():
    assert evaluate_in_node(
        f"""
        const timeline = window.AmbientCanvasTokenFieldTimeline;
        const {{ frameAt }} = createRenderer(1920, 1080, 0);
        const lastFrameSeconds =
          timeline.cycleDurationSeconds - 1 / {CAPTURE_FRAMES_PER_SECOND};
        process.stdout.write(JSON.stringify(
          frameAt(0) === frameAt(lastFrameSeconds),
        ));
        """
    )


def test_a_recording_chunk_continues_the_same_field_at_its_start_offset():
    assert evaluate_in_node(
        f"""
        const continuous = createRenderer(1920, 1080, 0);
        const chunk = createRenderer(1920, 1080, {RECORDED_CHUNK_SECONDS});
        process.stdout.write(JSON.stringify(
          continuous.frameAt({RECORDED_CHUNK_SECONDS + 7.25}) === chunk.frameAt(7.25),
        ));
        """
    )


def test_the_scene_records_as_one_sequence_longer_than_a_chunk():
    recording_source = evaluate_in_node(
        """
        process.stdout.write(JSON.stringify(
          createRenderer(1920, 1080, 0).renderer.resolveRecordingSource(),
        ));
        """
    )
    assert recording_source["sequence"] == "token-field"
    assert recording_source["durationSeconds"] > RECORDED_CHUNK_SECONDS


def test_the_field_layout_is_deterministic_and_stays_inside_its_grid():
    layout_report = evaluate_in_node(
        """
        const layoutModule = window.AmbientCanvasTokenFieldLayout;
        const vocabulary = window.AmbientCanvasTokenFieldVocabulary;
        const timeline = window.AmbientCanvasTokenFieldTimeline;
        const grids = [
          { columnCount: 160, rowCount: 44 },
          { columnCount: 287, rowCount: 44 },
          { columnCount: 40, rowCount: 11 },
        ];
        const reports = grids.map((grid) => {
          const first = layoutModule.buildTokenFieldLayout(grid, timeline.GENERATION_COUNT, vocabulary);
          const second = layoutModule.buildTokenFieldLayout(grid, timeline.GENERATION_COUNT, vocabulary);
          const glyphCount = first.glyphs.length;
          return first.generations.map((generation, index) => ({
            repeatable:
              JSON.stringify(Array.from(generation.wordGlyphIndices)) ===
                JSON.stringify(Array.from(second.generations[index].wordGlyphIndices)) &&
              JSON.stringify(Array.from(generation.clearingOrder)) ===
                JSON.stringify(Array.from(second.generations[index].clearingOrder)),
            sized: generation.clearingOrder.length === grid.columnCount * grid.rowCount,
            ordersInRange: generation.clearingOrder.every((order) => order >= 0 && order <= 1),
            glyphsInRange:
              generation.wordGlyphIndices.every((glyph) => glyph >= -1 && glyph < glyphCount) &&
              generation.noiseGlyphIndices.every((glyph) => glyph >= -1 && glyph < glyphCount),
            carriesWords: generation.wordGlyphIndices.some((glyph) => glyph >= 0),
          }));
        });
        process.stdout.write(JSON.stringify(reports.flat()));
        """
    )
    assert layout_report
    for generation_report in layout_report:
        assert all(generation_report.values()), generation_report
