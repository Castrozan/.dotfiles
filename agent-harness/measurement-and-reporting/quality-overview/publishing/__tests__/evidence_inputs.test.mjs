import assert from "node:assert/strict";
import { test } from "node:test";
import { conventionalInputs } from "../evidence_inputs.mjs";

function contextForPythonEvidence(stepName, conclusion = "success") {
  const startedAt = "2026-10-16T00:01:00Z";
  const completedAt = "2026-10-16T00:02:00Z";
  const producer = {
    jobId: 41,
    jobName: "qml-and-python-tests",
    runAttempt: 2,
    startedAt,
    completedAt,
  };
  return {
    workflow: { runId: "31", runUrl: "https://example.test/runs/31" },
    jobs: [
      {
        id: 41,
        name: producer.jobName,
        steps: [
          {
            name: stepName,
            status: "completed",
            conclusion,
            started_at: startedAt,
            completed_at: completedAt,
          },
        ],
      },
    ],
    artifacts: {
      "python-junit": { id: 51, producer },
      "python-coverage": { id: 52, producer },
    },
  };
}

test("Python evidence uses the aggregate combine step and its attempt", () => {
  const context = contextForPythonEvidence("Combine Python evidence");
  const inputs = conventionalInputs(context, "https://example.test/").filter(
    (input) => input.id.startsWith("python-"),
  );
  assert.deepEqual(
    inputs.map((input) => input.format),
    ["junit", "junit", "cobertura"],
  );
  assert.deepEqual(
    inputs.map((input) => input.path),
    [
      "../raw/python-junit/pytest-unit.xml",
      "../raw/python-junit/pytest-integration.xml",
      "../raw/python-coverage/python-coverage.xml",
    ],
  );
  for (const input of inputs) {
    assert.equal(input.run.id, `31.2:${input.id}`);
    assert.equal(input.run.startedAt, context.jobs[0].steps[0].started_at);
    assert.equal(input.run.completedAt, context.jobs[0].steps[0].completed_at);
  }
});

test("the previous execution step cannot impersonate the aggregate producer", () => {
  const context = contextForPythonEvidence("Run Python tests");
  const inputs = conventionalInputs(context, "").filter((input) =>
    input.id.startsWith("python-"),
  );
  assert.ok(inputs.every((input) => input.format === "malformed"));
});

test("a failed combine step retains available native diagnostic evidence", () => {
  const context = contextForPythonEvidence(
    "Combine Python evidence",
    "failure",
  );
  const inputs = conventionalInputs(context, "").filter((input) =>
    input.id.startsWith("python-"),
  );
  assert.deepEqual(
    inputs.map((input) => input.format),
    ["junit", "junit", "cobertura"],
  );
});
