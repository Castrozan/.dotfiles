import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { test } from "node:test";
import { artifactInputs } from "../artifact_inputs.mjs";
import { unmeasuredCapabilities } from "../../unmeasured_capabilities.mjs";
import { fixture } from "./fixture.mjs";

const { overviewManifestSchema } = await import(
  pathToFileURL(
    join(process.env.VERDR_EVALUATOR_ROOT, "dist/overview/manifest.js"),
  ).href
);

function frozenManifest(context) {
  const scope = {
    name: "Owned artifact fixture",
    tier: "artifact",
    platform: "linux",
    exclusions: [],
  };
  const targets = ["claude", "codex", "opencode", "pi", "hermes"];
  return {
    schemaVersion: 1,
    name: "Owned frozen inventory",
    subject: {
      repository: context.workflow.repository,
      revision: context.workflow.revision,
      artifactDigest: "b".repeat(64),
    },
    inputs: [
      ...[
        "source-preservation",
        ...targets.map((target) => `${target}-artifact`),
      ].map((id) => ({
        id,
        label: id,
        format: "verdr",
        target: null,
        scope,
        maxAgeSeconds: 60,
        path: `${id}/report.json`,
        sourceUri: `../${id}/report.json`,
        runUrl: context.workflow.runUrl,
        suiteDigest: "c".repeat(64),
        cases: [{ id: "owned-case", kind: "file", target: null }],
      })),
      ...unmeasuredCapabilities(targets, scope),
    ],
  };
}

for (const corruption of [
  "none",
  "revision",
  "run",
  "escape",
  "gap",
  "format",
]) {
  test(`frozen artifact inventory control: ${corruption}`, async (testContext) => {
    const { context, downloads } = await fixture(testContext, false);
    context.artifacts["verdr-artifact-evidence"] = { id: 1, reason: null };
    const manifest = frozenManifest(context);
    if (corruption === "revision") manifest.subject.revision = "f".repeat(40);
    if (corruption === "run")
      manifest.inputs[0].runUrl = "https://example.test/foreign-run";
    if (corruption === "escape") manifest.inputs[0].path = "../foreign.json";
    if (corruption === "gap") manifest.inputs.pop();
    if (corruption === "format")
      manifest.inputs.push({
        id: "foreign",
        label: "Foreign",
        format: "junit",
        target: null,
        scope: manifest.inputs[0].scope,
        maxAgeSeconds: 60,
        path: "/foreign.xml",
        sourceUri: "https://example.test/foreign.xml",
        run: {
          id: "foreign",
          url: context.workflow.runUrl,
          startedAt: context.workflow.startedAt,
          completedAt: context.workflow.completedAt,
        },
      });
    const directory = join(
      downloads,
      "verdr-artifact-evidence/artifact-evidence",
    );
    await mkdir(directory, { recursive: true });
    await writeFile(join(directory, "manifest.json"), JSON.stringify(manifest));
    const result = await artifactInputs(
      context,
      downloads,
      "https://example.test/report/",
      overviewManifestSchema,
    );
    assert.equal(result.inputs.length, 28);
    if (corruption === "none") {
      assert.equal(result.artifactDigest, "b".repeat(64));
      assert.equal(
        result.inputs.filter((input) => input.format === "verdr").length,
        6,
      );
      assert.ok(
        result.inputs[0].path.startsWith(
          "../raw/verdr-artifact-evidence/artifact-evidence/",
        ),
      );
    } else {
      assert.equal(result.artifactDigest, undefined);
      assert.equal(
        result.inputs.filter((input) => input.format === "malformed").length,
        6,
      );
      assert.equal(
        result.inputs.filter((input) => input.format === "unmeasured").length,
        22,
      );
    }
  });
}
