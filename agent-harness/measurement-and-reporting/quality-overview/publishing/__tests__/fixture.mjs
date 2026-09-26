import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const scripts = dirname(dirname(fileURLToPath(import.meta.url)));
const evaluator = process.env.VERDR_EVALUATOR_ROOT;
assert.ok(
  evaluator,
  "VERDR_EVALUATOR_ROOT must name the pinned built evaluator",
);
export const junit =
  '<testsuite name="owned" tests="3" failures="1" errors="0" skipped="1"><testcase name="pass"/><testcase name="fail"><failure message="owned negative control"/></testcase><testcase name="skip"><skipped/></testcase></testsuite>';
const cobertura =
  '<coverage lines-covered="1" lines-valid="2"><packages><package name="owned"><classes><class name="Owned" filename="owned.py"><lines><line number="1" hits="1"/><line number="2" hits="0"/></lines></class></classes></package></packages></coverage>';

export async function fixture(testContext, includeReports) {
  const root = await mkdtemp(join(tmpdir(), "verdr-publisher-control-"));
  testContext.after(() => rm(root, { recursive: true, force: true }));
  const now = Date.now();
  const startedAt = new Date(now - 20000).toISOString();
  const completedAt = new Date(now - 10000).toISOString();
  const context = {
    workflow: {
      repository: "Castrozan/.dotfiles",
      revision: "a".repeat(40),
      runId: "1",
      runAttempt: 1,
      runUrl: "https://github.com/Castrozan/.dotfiles/actions/runs/1",
      conclusion: "failure",
      startedAt,
      completedAt,
    },
    jobs: [
      {
        name: "quick-tests",
        steps: [
          {
            name: "Run quick tests",
            status: "completed",
            started_at: startedAt,
            completed_at: completedAt,
          },
        ],
      },
      {
        name: "qml-and-python-tests",
        steps: [
          {
            name: "Run Python tests",
            status: "completed",
            started_at: startedAt,
            completed_at: completedAt,
          },
        ],
      },
    ],
    artifacts: Object.fromEntries(
      [
        "bats-junit",
        "python-junit",
        "python-coverage",
        "verdr-artifact-evidence",
      ].map((name) => [
        name,
        {
          id: includeReports && name !== "verdr-artifact-evidence" ? 1 : null,
          reason: "Owned absent artifact fixture",
        },
      ]),
    ),
  };
  const downloads = join(root, "downloads");
  await mkdir(downloads);
  if (includeReports) {
    for (const path of [
      "bats-junit/bats-unit/report.xml",
      "bats-junit/bats-integration/report.xml",
      "python-junit/pytest-unit.xml",
      "python-junit/pytest-integration.xml",
      "python-coverage/python-coverage.xml",
    ]) {
      await mkdir(dirname(join(downloads, path)), { recursive: true });
      await writeFile(
        join(downloads, path),
        path.startsWith("python-coverage") ? cobertura : junit,
      );
    }
  }
  return { root, downloads, context };
}

export async function build(input) {
  const contextPath = join(input.root, "context.json");
  const output = join(input.root, "output");
  await writeFile(contextPath, JSON.stringify(input.context));
  const execution = spawnSync(
    process.execPath,
    [
      join(scripts, "build_snapshot.mjs"),
      evaluator,
      contextPath,
      input.downloads,
      output,
    ],
    { encoding: "utf8", timeout: 20000 },
  );
  assert.equal(execution.status, 0, execution.stderr);
  return {
    output,
    payload: JSON.parse(await readFile(join(output, "payload.json"), "utf8")),
  };
}
