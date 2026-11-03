import json
import pathlib
import subprocess


RECORDING_PLAN_PATH = (
    pathlib.Path(__file__).resolve().parents[3]
    / "web/record/ambient-canvas-recording-plan.js"
)


def test_segment_assignment_balances_duration_and_is_independent_of_cache_inventory():
    source = r"""
global.window = global;
require('node:vm').runInThisContext(require('node:fs').readFileSync(process.argv[1], 'utf8'));
const plan = window.AmbientCanvasRecordingPlan;
const durations = [5, 30, 30, 30, 5, 5, 5, 5];
function resolveOwners(cached) {
  const assignments = Array.from({length: 4}, (_, index) => {
    const parameters = new URLSearchParams({workerIndex: String(index), workerCount: '4'});
    const worker = plan.resolveRecordingParameters(parameters).worker;
    return durations.map((durationSeconds, position) =>
      plan.assignSegmentRecording({durationSeconds}, worker, String(position), cached));
  });
  return durations.map((duration, position) =>
    assignments.flatMap((owned, workerIndex) => owned[position] ? [workerIndex] : []));
}
const owners = resolveOwners(new Set());
const cachedOwners = resolveOwners(new Set(['0']));
process.stdout.write(JSON.stringify({durations, owners, cachedOwners}));
"""
    completed = subprocess.run(
        ["node", "-e", source, str(RECORDING_PLAN_PATH)],
        check=True,
        text=True,
        capture_output=True,
        timeout=10,
    )
    outcome = json.loads(completed.stdout)
    assert all(len(owners) == 1 for owners in outcome["owners"])
    scheduled_seconds = [0] * 4
    for duration, owners in zip(outcome["durations"], outcome["owners"], strict=True):
        scheduled_seconds[owners[0]] += duration
    assert scheduled_seconds == [25, 30, 30, 30]
    assert outcome["cachedOwners"][0] == []
    assert outcome["cachedOwners"][1:] == outcome["owners"][1:]
