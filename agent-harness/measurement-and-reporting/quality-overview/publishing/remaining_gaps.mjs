import { unavailableInput } from "./evidence_inputs.mjs";

export function remainingGaps(context) {
  return [
    [
      "swift-tests",
      "Swift native tests",
      "tests",
      "Native Swift tests run without a supported testcase report in this overview.",
      "unmeasured",
    ],
    [
      "qml-tests",
      "QML native tests",
      "tests",
      "Native QML tests run without a supported testcase report in this overview.",
      "unmeasured",
    ],
    [
      "lua-tests",
      "Lua native tests",
      "tests",
      "Native Lua tests run without a supported testcase report in this overview.",
      "unmeasured",
    ],
    [
      "swift-coverage",
      "Swift coverage",
      "coverage",
      "Native Swift Cobertura coverage is produced but is not imported by this overview.",
      "unmeasured",
    ],
    [
      "mutation",
      "Mutation testing",
      "mutation",
      "This workflow does not execute a mutation-testing suite.",
      "unmeasured",
    ],
  ].map(([id, label, category, reason, format]) =>
    unavailableInput(
      {
        id,
        label,
        category,
        scope: {
          name: label,
          tier: "CI",
          platform: id.startsWith("swift") ? "darwin" : "linux",
          exclusions: [],
        },
      },
      context,
      format,
      reason,
    ),
  );
}
