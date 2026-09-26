import assert from "node:assert/strict";
import { readFile, stat } from "node:fs/promises";
import { isAbsolute, join } from "node:path";
import { unmeasuredCapabilities } from "../unmeasured_capabilities.mjs";
import {
  artifactScope,
  artifactTargets,
  unavailableInput,
} from "./evidence_inputs.mjs";

const descriptors = [
  {
    id: "source-preservation",
    label: "Source bytes and executable modes",
    target: null,
  },
  ...artifactTargets.map((target) => ({
    id: `${target}-artifact`,
    label: `${target} emitted package checks`,
    target,
  })),
];

const compareEntries = (left, right) =>
  JSON.stringify(left).localeCompare(JSON.stringify(right));

function unavailableArtifacts(context, format, reason) {
  return {
    artifactDigest: undefined,
    inputs: [
      ...descriptors.map((descriptor) =>
        unavailableInput(
          { ...descriptor, scope: artifactScope, category: "artifact" },
          context,
          format,
          reason,
        ),
      ),
      ...unmeasuredCapabilities(artifactTargets, artifactScope),
    ],
  };
}

export async function artifactInputs(
  context,
  downloads,
  detailsBaseUrl,
  manifestSchema,
) {
  const selection = context.artifacts["verdr-artifact-evidence"];
  if (!selection?.id)
    return unavailableArtifacts(
      context,
      "missing",
      selection?.reason ?? "Artifact evidence was not selected",
    );
  const prefix = "verdr-artifact-evidence/artifact-evidence";
  try {
    const path = join(downloads, prefix, "manifest.json");
    assert.ok(
      (await stat(path)).size <= 16777216,
      "Frozen inventory exceeds the input limit",
    );
    const manifest = manifestSchema.parse(
      JSON.parse(await readFile(path, "utf8")),
    );
    assert.equal(
      manifest.subject.repository,
      context.workflow.repository,
      "Frozen inventory repository differs from the run",
    );
    assert.equal(
      manifest.subject.revision,
      context.workflow.revision,
      "Frozen inventory revision differs from the run",
    );
    const expectedGaps = unmeasuredCapabilities(artifactTargets, artifactScope);
    assert.deepEqual(
      manifest.inputs
        .map((input) => [input.id, input.format])
        .sort(compareEntries),
      [
        ...descriptors.map((input) => [input.id, "verdr"]),
        ...expectedGaps.map((input) => [input.id, "unmeasured"]),
      ].sort(compareEntries),
      "Frozen inventory differs from the complete expected evidence inventory",
    );
    const inputs = manifest.inputs.map((input) => {
      if (input.format !== "verdr") return input;
      assert.ok(
        !isAbsolute(input.path) && !input.path.split(/[\\/]/).includes(".."),
        "Report path escapes the downloaded evidence",
      );
      assert.equal(
        input.runUrl,
        context.workflow.runUrl,
        "Report run URL differs from the producing run",
      );
      const path = `raw/${prefix}/${input.path}`;
      return {
        ...input,
        path: `../${path}`,
        sourceUri: `${detailsBaseUrl}${path}`,
      };
    });
    return { artifactDigest: manifest.subject.artifactDigest, inputs };
  } catch (error) {
    return unavailableArtifacts(
      context,
      error.code === "ENOENT" ? "missing" : "malformed",
      error.message,
    );
  }
}
