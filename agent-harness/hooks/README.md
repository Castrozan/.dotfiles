# Shared hook policy and native contracts

Rulesync generates Claude, Codex and OpenCode registrations from one declarative source. The shared Python runtime owns
policy, handler ordering and outcome merging. Native transports own tool names, argument fields and response formats.
Changing a policy therefore does not require reproducing its logic in every harness.

Arbitrary MCP arguments and nested tool values remain opaque. Transports translate only fields belonging to a verified
native tool schema. A denied operation carries its reason and cannot carry an input rewrite; rewrites require an
explicit allow. Executable contracts cover these boundaries independently of registration generation.

## Capability limits

| #   | Harness     | Integration                                     | Supported behavior                                                                  |
| --- | ----------- | ----------------------------------------------- | ----------------------------------------------------------------------------------- |
| 1   | Claude Code | Rulesync native command hooks                   | Session context, tool decisions and rewrites, tool feedback, reply continuation     |
| 2   | Codex       | Rulesync native command hooks                   | Session context, tool decisions and rewrites, tool feedback, reply continuation     |
| 3   | OpenCode    | Rulesync V2 plugin and schema transport         | Session context, tool decisions and rewrites, post-tool context, reply continuation |
| 4   | Pi          | Agent Plugins loader and native reply extension | Shared skills and MCP; bounded reply continuation through the native extension      |
| 5   | Hermes      | Native shell hooks and schema transport         | Tool denial and argument modification; post-tool observation                        |

The generated OpenCode V2 plugin does not consume pre-tool `additionalContext`. Hermes post-tool hooks are observers:
their returned values cannot change completed execution or add model context. Pi's portable plugin loader does not
execute command hooks. These limits belong to the installed native integrations; copying a hook file into a complete
plugin does not extend a loader's capabilities.

Native acceptance tests exercise the receiving runtime, including denied side effects, input rewrites, context delivery
and continuation bounds. Registration checks alone cannot prove that a harness interpreted a response. A supported
capability needs a native contract when it is extended.

## Dependency choice

Rulesync and the shared policy runtime retain their existing responsibilities. The internal TypeScript toolkit provides
a useful policy/transport separation, but adopting it would add a private package without proving native support across
the configured harnesses. The public `agent-hooks` Python package covers Claude and Codex, so it does not replace the
other native edges.

The evaluated `@hsingjui/pi-hooks` 0.0.2 package provides the missing Pi JSON lifecycle bridge, but its timeout terminates only
the shell and leaves descendants alive; it also accumulates output without a bound. It cannot replace a deployed
integration until those resource contracts pass. Dependency changes require native SDK verification of the pinned
package independently of policy changes.

Codex's private app-server sends diagnostics to a bounded sink rather than the terminal owned by its remote TUI. The
launcher owns that descriptor and teardown; hook policy cannot repair a backend sharing the terminal's stderr.

Authoritative native protocols: https://learn.chatgpt.com/docs/hooks,
https://code.claude.com/docs/en/hooks, https://github.com/anomalyco/opencode/tree/dev/packages/plugin,
https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md,
https://github.com/NousResearch/hermes-agent/blob/main/agent/shell_hooks.py.
