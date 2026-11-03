import pathlib
import subprocess

import pytest

FINGERPRINT_SOURCE = (
    pathlib.Path(__file__).resolve().parents[3]
    / "web/record/ambient-canvas-recording-fingerprint.js"
)


@pytest.mark.parametrize(
    "request_method",
    ["fetchSegmentFingerprintInputs", "fetchRecordedSegmentFingerprints"],
)
@pytest.mark.parametrize("failure", ["http", "network"])
def test_metadata_failure_aborts_instead_of_using_empty_source_inputs(
    request_method, failure
):
    source = r"""
global.window = global;
global.fetch = async () => {
  if (process.argv[3] === 'network') throw new Error('disconnected');
  return {ok: false, status: 500};
};
eval(require('fs').readFileSync(process.argv[1], 'utf8'));
window.AmbientCanvasRecordingFingerprint[process.argv[2]]('http://localhost/upload')
  .then(() => { process.exitCode = 1; })
  .catch(() => { process.stdout.write('aborted'); });
"""
    completed = subprocess.run(
        ["node", "-e", source, str(FINGERPRINT_SOURCE), request_method, failure],
        check=True,
        text=True,
        capture_output=True,
        timeout=10,
    )
    assert completed.stdout == "aborted"
