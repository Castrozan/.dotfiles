import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { test } from "node:test";
import { fixture, build, privateBaseUrl, runBuild } from "./fixture.mjs";

function assertRefusedBeforeOutput(execution, output) {
  assert.notEqual(execution.status, 0);
  assert.match(execution.stderr, /REPORT_ARTIFACT_BASE_URL/);
  assert.equal(existsSync(output), false);
}

test("a configured private base yields the versioned attempt details URL", async (context) => {
  const input = await fixture(context, true);
  const { payload } = await build(input);
  assert.equal(payload.detailsBaseUrl, `${privateBaseUrl}overview/1/1/`);
});

test("a missing configured base is refused before any output is written", async (context) => {
  const input = await fixture(context, true);
  const { execution, output } = await runBuild(input, {});
  assertRefusedBeforeOutput(execution, output);
});

const malformedBaseUrls = [
  "",
  "reports.example.test/private/reports/",
  "http://reports.example.test/private/reports/",
  "https://reports.example.test/private/reports",
  "https://user:secret@reports.example.test/private/reports/",
  "https://@reports.example.test/private/reports/",
  "https://reports.example.test/private/reports/?token=1",
  "https://reports.example.test/private/reports/#fragment",
  "https://reports.example.test/private/reports/\n",
  "https://reports.example.test/private/ reports/",
  "https:///private/reports/",
  "https://reports.example.test:65536/reports/",
  "https://reports.example.test:invalid/reports/",
  "https://[invalid]/reports/",
  "https://reports.example.test:0/reports/",
  "https://reports.example.test/\\reports/",
];

for (const baseUrl of malformedBaseUrls) {
  test(`configured base ${JSON.stringify(baseUrl)} is refused before any output is written`, async (context) => {
    const input = await fixture(context, true);
    const { execution, output } = await runBuild(input, {
      REPORT_ARTIFACT_BASE_URL: baseUrl,
    });
    assertRefusedBeforeOutput(execution, output);
  });
}
