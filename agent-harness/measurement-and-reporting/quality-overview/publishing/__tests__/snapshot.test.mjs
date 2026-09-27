import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { test } from "node:test";
import { fixture, build, junit } from "./fixture.mjs";

test("missing producer outputs retain all declared capabilities without a digest or pass", async (context) => {
  const input = await fixture(context, false);
  const { payload } = await build(input);
  assert.equal(payload.overview.evidence.length, 38);
  assert.equal(
    payload.overview.evidence.filter((item) => item.validity === "missing")
      .length,
    11,
  );
  assert.ok(payload.overview.evidence.every((item) => !item.usable));
  assert.equal(payload.overview.subject.artifactDigest, undefined);
  assert.equal(payload.workflow.conclusion, "failure");
});

test("native XML outcomes and hashes survive beside missing artifact evidence", async (context) => {
  const input = await fixture(context, true);
  const { payload, output } = await build(input);
  const tests = payload.overview.evidence.filter(
    (item) => item.measurement?.kind === "tests",
  );
  assert.equal(tests.length, 4);
  for (const evidence of tests) {
    assert.equal(evidence.outcome, "failed");
    assert.equal(evidence.usable, true);
    assert.deepEqual(evidence.measurement.counts, {
      total: 3,
      passed: 1,
      failed: 1,
      error: 0,
      skipped: 1,
    });
    assert.equal(
      evidence.source.sha256,
      createHash("sha256").update(junit).digest("hex"),
    );
  }
  const coverage = payload.overview.evidence.find(
    (item) => item.id === "python-coverage",
  );
  assert.equal(coverage.outcome, "measured");
  assert.deepEqual(coverage.measurement.lineCoverage, { covered: 1, total: 2 });
  assert.equal(
    await readFile(
      join(output, "site/raw/python-junit/pytest-unit.xml"),
      "utf8",
    ),
    junit,
  );
  assert.ok(tests.every((item) => item.run.id.startsWith("1.1:")));
});

test("malformed frozen inventory does not hide working tests or become a pass", async (context) => {
  const input = await fixture(context, true);
  const directory = join(
    input.downloads,
    "verdr-artifact-evidence/artifact-evidence",
  );
  await mkdir(directory, { recursive: true });
  await writeFile(join(directory, "manifest.json"), "{broken-json");
  input.context.artifacts["verdr-artifact-evidence"] = { id: 2, reason: null };
  const { payload } = await build(input);
  const malformed = payload.overview.evidence.filter(
    (item) => item.validity === "malformed",
  );
  assert.equal(malformed.length, 6);
  assert.ok(
    malformed.every((item) => !item.usable && item.measurement === null),
  );
  assert.equal(
    payload.overview.evidence.filter((item) => item.usable).length,
    5,
  );
});

test("missing XML after download remains missing despite a valid artifact selection", async (context) => {
  const input = await fixture(context, true);
  await rm(join(input.downloads, "python-junit/pytest-unit.xml"));
  const { payload } = await build(input);
  const evidence = payload.overview.evidence.find(
    (item) => item.id === "python-unit",
  );
  assert.equal(evidence.validity, "missing");
  assert.equal(evidence.usable, false);
  assert.equal(evidence.measurement, null);
});

test("a partial retry retains original evidence times and attempt identity", async (context) => {
  const input = await fixture(context, true);
  input.context.workflow.runAttempt = 2;
  input.context.workflow.startedAt = new Date(Date.now() - 5000).toISOString();
  input.context.workflow.completedAt = new Date().toISOString();
  const { payload } = await build(input);
  const evidence = payload.overview.evidence.find(
    (item) => item.id === "python-unit",
  );
  assert.equal(evidence.usable, true);
  assert.equal(evidence.run.id, "1.1:python-unit");
  assert.equal(
    evidence.run.startedAt,
    input.context.jobs[1].steps[0].started_at,
  );
  assert.equal(payload.workflow.runAttempt, 2);
});

test("required evidence completeness accepts failed tests but rejects missing measurements", async () => {
  const { incompleteEvidence } = await import("../check_completeness.mjs");
  const { requiredEvidenceIds } = await import("../evidence_inputs.mjs");
  const evidence = requiredEvidenceIds.map((id) => ({
    id,
    usable: true,
    outcome: "failed",
  }));
  assert.deepEqual(incompleteEvidence({ evidence }), []);
  evidence[0].usable = false;
  assert.deepEqual(incompleteEvidence({ evidence }), ["source-preservation"]);
  assert.equal(incompleteEvidence({ evidence: [] }).length, 11);
});
