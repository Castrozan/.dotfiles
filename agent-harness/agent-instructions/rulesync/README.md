# Rulesync configuration generation

Rulesync compiles the shared core instructions and the public Claude Code and
OpenCode agent definitions during the Nix build. Native registration and activation
remain in the harness modules. Sentry continues to produce plugin discovery from
the complete package; no private marketplace or replacement hook runtime is added.

| Configuration                | Authoritative input                                              | Delivery                                                                                                            |
| ---------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Shared core                  | Existing core instructions                                       | Rulesync root rules, deployed at the existing Claude, Codex and OpenCode global paths and composed into Hermes SOUL |
| Public agents                | Canonical Rulesync subagents                                     | Native Claude and OpenCode definitions with explicit target metadata                                                |
| Skills and supporting assets | Existing skill catalog and instruction projection                | Complete package, with original discovery scopes and opaque assets preserved                                        |
| MCP                          | Existing portable server declarations                            | Sentry discovery and existing native launchers                                                                      |
| Hooks and workflows          | Existing event registrations and executable workflow definitions | Existing native runtimes and required adapters                                                                      |

The generated configuration and its Rulesync inputs travel inside the production
plugin. Generated native agent metadata is checked against each canonical target
section; the body is preserved apart from boundary newlines. Native OpenCode names
come from the canonical definition. Core instruction bytes remain unchanged.
Interactive instructions and repository instructions retain their existing scope.

## Build isolation and validation

The dependency lock pins Rulesync. Generation uses project mode in fresh output
directories with isolated home and Hermes profile roots. Home Manager selects the
native deployment paths; the generator never operates on a live profile.

Rulesync can skip malformed subagents with exit status zero. The build therefore
requires every expected native file and rejects unexpected outputs or changed core
instructions. Failed builds discard their partial output. The integration check
reproduces the upstream omission before proving rejection and cleanup.

## Retained boundaries

Rulesync reconstructs skill frontmatter and does not preserve arbitrary fields.
Skill payloads remain with the existing complete-package projection. Its generated
OpenCode hooks do not transport the event and decision protocol required by our
guards. Community replacements also need native failure and lifecycle evidence
before they can replace those adapters.

The Claude-to-OpenCode converter remains for private agent definitions. Public
agents use Rulesync. Executable workflow commands retain their workflow engine;
they are not converted into prompt files or skills. Receiving an extension does
not establish that a harness executes it.

Codex portable hook loading, Hermes hook translation and reply correction retain
their existing capability limits. Configuration discovery, native execution and
model adherence are separate claims. An unsupported replacement leaves the working
adapter in place and records the unmet removal condition.

## Verification

The Rulesync integration check verifies core bytes, native agent metadata and
bodies, expected inventory, malformed-source rejection and cleanup. The production
package check compares every declared artifact and all executable bits. Native
acceptance uses the final emitted files and exact installed clients in isolated
profiles; parsing or callback fixtures alone do not prove hook execution.

Relevant upstream contracts are [Rulesync plugin packaging](https://rulesync.dyoshikawa.com/guide/plugin-packaging.html)
and [supported targets](https://rulesync.dyoshikawa.com/reference/supported-tools.html).
