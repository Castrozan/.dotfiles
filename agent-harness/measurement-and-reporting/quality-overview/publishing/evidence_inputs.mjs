export const artifactTargets = ["claude", "codex", "opencode", "pi", "hermes"];

export const artifactScope = {
  name: "CI emitted complete production package",
  tier: "artifact",
  platform: "linux",
  exclusions: [
    "deployed host profiles",
    "model turns",
    "MCP invocation",
    "browser processes",
    "instruction adherence",
  ],
};

export function unavailableInput(descriptor, context, format, reason) {
  return {
    id: descriptor.id,
    label: descriptor.label,
    target: descriptor.target ?? null,
    scope: descriptor.scope,
    maxAgeSeconds: 172800,
    format,
    category: descriptor.category,
    reason,
    sourceUri: context.workflow.runUrl,
  };
}

function producingJob(context, jobName, producer) {
  if (!producer || producer.jobName !== jobName) return null;
  const jobs = context.jobs.filter((job) => job.name === jobName);
  if (jobs.length !== 1 || jobs[0].id !== producer.jobId) return null;
  return jobs[0];
}

function stepIsWithinProducerInterval(started, completed, producer) {
  return !(
    started < Date.parse(producer.startedAt) ||
    completed < started ||
    completed > Date.parse(producer.completedAt)
  );
}

function producingStepIsValid(step, producer, started, completed) {
  if (
    step.status !== "completed" ||
    !Number.isFinite(started) ||
    !Number.isFinite(completed)
  )
    return false;
  return stepIsWithinProducerInterval(started, completed, producer);
}

function producingStep(context, jobName, stepName, producer) {
  const job = producingJob(context, jobName, producer);
  if (!job) return null;
  const steps = job.steps.filter((step) => step.name === stepName);
  if (steps.length !== 1) return null;
  const step = steps[0];
  const started = Date.parse(step.started_at);
  const completed = Date.parse(step.completed_at);
  if (!producingStepIsValid(step, producer, started, completed)) return null;
  return step;
}

const testInputs = [
  [
    "bats-unit",
    "Bats unit tests",
    "bats-junit",
    "bats-unit/report.xml",
    "quick-tests",
    "Run quick tests",
    "unit",
  ],
  [
    "bats-integration",
    "Bats integration tests",
    "bats-junit",
    "bats-integration/report.xml",
    "quick-tests",
    "Run quick tests",
    "integration",
  ],
  [
    "python-unit",
    "Python unit tests",
    "python-junit",
    "pytest-unit.xml",
    "qml-and-python-tests",
    "Run Python tests",
    "unit",
  ],
  [
    "python-integration",
    "Python integration tests",
    "python-junit",
    "pytest-integration.xml",
    "qml-and-python-tests",
    "Run Python tests",
    "integration",
  ],
  [
    "python-coverage",
    "Python line and branch coverage",
    "python-coverage",
    "python-coverage.xml",
    "qml-and-python-tests",
    "Run Python tests",
    "unit and integration",
  ],
];

function conventionalInputDescriptor(id, label, tier) {
  const coverage = id === "python-coverage";
  const scope = {
    name: coverage
      ? "Python under agent-harness, machine-configuration and repository"
      : label,
    tier,
    platform: "linux",
    exclusions: coverage
      ? ["__tests__", "conftest.py", "non-Python files"]
      : ["other languages and tiers"],
  };
  return {
    coverage,
    scope,
    descriptor: { id, label, scope, category: coverage ? "coverage" : "tests" },
  };
}

function conventionalInput(context, detailsBaseUrl, input) {
  const [id, label, artifact, file, job, stepName, tier] = input;
  const { coverage, scope, descriptor } = conventionalInputDescriptor(id, label, tier);
  const selection = context.artifacts[artifact];
  if (!selection?.id)
    return unavailableInput(
      descriptor,
      context,
      "missing",
      selection?.reason ?? "Producer artifact was not selected",
    );
  const step = producingStep(context, job, stepName, selection.producer);
  if (!step)
    return unavailableInput(
      descriptor,
      context,
      "malformed",
      "Producing step has no usable timestamp interval for this attempt",
    );
  const path = `raw/${artifact}/${file}`;
  return {
    id,
    label,
    scope,
    target: null,
    maxAgeSeconds: 172800,
    format: coverage ? "cobertura" : "junit",
    path: `../${path}`,
    sourceUri: `${detailsBaseUrl}${path}`,
    run: {
      id: `${context.workflow.runId}.${selection.producer.runAttempt}:${id}`,
      url: context.workflow.runUrl,
      startedAt: step.started_at,
      completedAt: step.completed_at,
    },
  };
}

export function conventionalInputs(context, detailsBaseUrl) {
  return testInputs.map((input) =>
    conventionalInput(context, detailsBaseUrl, input),
  );
}

export const requiredEvidenceIds = [
  "source-preservation",
  ...artifactTargets.map((target) => `${target}-artifact`),
  ...testInputs.map(([id]) => id),
];
