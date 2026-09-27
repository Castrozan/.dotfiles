# Rulesync configuration generation

Rulesync compiles the shared core instructions and the public Claude Code and
OpenCode agent definitions during the Nix build. It also generates Claude Code,
Codex and OpenCode V2 hooks from the shared hook source. Nix owns native deployment
and activation; Python dispatchers retain policy decisions. Sentry continues to
produce plugin discovery from the complete package.

| Configuration                | Authoritative input                               | Delivery                                                                                                            |
| ---------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Shared core                  | Existing core instructions                        | Rulesync root rules, deployed at the existing Claude, Codex and OpenCode global paths and composed into Hermes SOUL |
| Public agents                | Canonical Rulesync subagents                      | Native Claude and OpenCode definitions with explicit target metadata                                                |
| Skills and supporting assets | Existing skill catalog and instruction projection | Complete package, with original discovery scopes and opaque assets preserved                                        |
| MCP                          | Existing portable server declarations             | Sentry discovery and existing native launchers                                                                      |
| Hooks                        | Shared Rulesync hook source with target overrides | Claude settings, managed Codex requirements and the generated OpenCode V2 plugin                                    |
| Workflows                    | Executable workflow definitions                   | Existing native workflow runtimes                                                                                   |

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
Skill payloads remain with the existing complete-package projection. The immutable
Rulesync fork generates the OpenCode V2 command runtime when the source selects
`opencode.apiVersion: 2`. The policy transport converts native tool arguments to
the existing dispatcher protocol and translates replacement inputs back. Runtime
generation belongs to Rulesync; policy normalization remains in the harness.

Claude settings merge generated registrations with Herdr's native session hook.
Codex's generated JSON becomes `/etc/codex/requirements.toml`, preserving managed
hook trust. The former OpenCode bridge is removed during activation so each event
has one command registration. Commands retain target-specific timeout budgets and
the private per-host prohibited-word exemptions.

OpenCode V2 has no native Stop veto. Its generated adapter observes completion and
requests at most one synthetic correction, while Claude and Codex use native Stop
decisions. Pre-tool context injection remains unsupported by the OpenCode adapter.

The Claude-to-OpenCode converter remains for private agent definitions. Public
agents use Rulesync. Executable workflow commands retain their workflow engine;
they are not converted into prompt files or skills. Receiving an extension does
not establish that a harness executes it.

Hermes hook translation and Pi reply correction retain their existing runtimes.
Configuration discovery, native execution and model adherence are separate claims.

## Verification

The Rulesync integration check verifies core bytes, native agent metadata and
bodies, expected inventory, malformed-source rejection and cleanup. The production
package check compares every declared artifact and all executable bits. Native
acceptance uses the final emitted files and exact installed clients in isolated
profiles; parsing or callback fixtures alone do not prove hook execution.
Registration checks read the generated Claude JSON and managed Codex TOML, including
event inventory, dispatchers, timeouts, matchers, and the Herdr session registration.

Relevant upstream contracts are [Rulesync plugin packaging](https://rulesync.dyoshikawa.com/guide/plugin-packaging.html)
and [supported targets](https://rulesync.dyoshikawa.com/reference/supported-tools.html).
