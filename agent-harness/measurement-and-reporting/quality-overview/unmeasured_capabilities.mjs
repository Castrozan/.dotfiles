const capabilities = [
  [
    "deployed-installation",
    "Deployed installation",
    "artifact",
    "CI measures an emitted package; no deployed user profile is read.",
  ],
  [
    "mcp-invocation",
    "MCP invocation",
    "artifact",
    "Production services and browser processes are outside this credential-free CI scope.",
  ],
  [
    "hook-execution",
    "Hook execution",
    "artifact",
    "Discovery does not establish native hook event delivery.",
  ],
  [
    "instruction-adherence",
    "Instruction adherence",
    "instruction",
    "No model turns or matched instruction experiment execute in this workflow.",
  ],
];

export function unmeasuredCapabilities(targets, scope) {
  const inputs = targets.flatMap((target) =>
    capabilities.map(([id, label, category, reason]) => ({
      id: `${target}-${id}`,
      label: `${target} ${label}`,
      target,
      scope,
      maxAgeSeconds: 172800,
      format: "unmeasured",
      category,
      reason,
    })),
  );
  for (const [target, reason] of [
    [
      "claude",
      "Native reload can initialize emitted MCP servers; this CI profile does not permit server startup.",
    ],
    [
      "hermes",
      "A pinned Hermes interpreter is not provisioned in this CI workflow.",
    ],
  ])
    inputs.push({
      id: `${target}-discovery`,
      label: `${target} native discovery`,
      target,
      scope,
      maxAgeSeconds: 172800,
      format: "unmeasured",
      category: "artifact",
      reason,
    });
  return inputs;
}
