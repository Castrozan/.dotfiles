import assert from "node:assert/strict";
import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";
import { compactEvidence } from "../compact_evidence.mjs";

test("compact generated evidence without changing values or raw source bytes", async (context) => {
  const site = await mkdtemp(join(tmpdir(), "compact-evidence-"));
  context.after(() => rm(site, { recursive: true, force: true }));
  await mkdir(join(site, "evidence"));
  await mkdir(join(site, "raw"));
  const evidence = {
    source: { sha256: "abc" },
    details: Array(50000).fill({ line: 1, hits: 0 }),
  };
  const pretty = JSON.stringify(evidence, null, 2);
  await writeFile(join(site, "evidence/coverage.json"), pretty);
  await writeFile(join(site, "raw/source.json"), pretty);
  await compactEvidence(site);
  const compact = await readFile(join(site, "evidence/coverage.json"), "utf8");
  assert.deepEqual(JSON.parse(compact), evidence);
  assert.equal(compact, JSON.stringify(evidence));
  assert.ok(Buffer.byteLength(compact) < Buffer.byteLength(pretty));
  assert.equal(await readFile(join(site, "raw/source.json"), "utf8"), pretty);
});
