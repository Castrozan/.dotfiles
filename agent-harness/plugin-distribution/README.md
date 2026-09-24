# Complete plugin distribution

The unit of distribution is the complete [Agent Plugins package](https://agent-plugins.org/specification). Every source
file, including hooks, agents, commands, workflows, binaries, native manifests and client extensions, reaches the output.
Git metadata is excluded. Distribution does not maintain an artifact allowlist or reinterpret unfamiliar extensions.
The receiving loader owns component discovery, execution and extension semantics.

Production composition lives in `../agent-instructions/production-plugin`. Its inventory maps every selected source
artifact to the complete package, including indexed and repository skills outside global discovery. Harness modules
register that package and retain native bridges for capabilities their portable loaders do not execute. Native external
marketplace selections and workspace enablement remain with their existing owners; cached plugins are not promoted into
global scope. The old Claude-to-Codex and Claude-to-OpenCode component copiers are retired.

Deployment archives retired mutable projections under `~/.local/state/agent-plugins/retired-projections` once per target,
preserving local changes outside discovery. Home Manager removes its superseded immutable links. Autonomous agent skill
sets and repository instruction surfaces retain their native scoped interfaces, with shared references into the package.

`agent-plugin-build SOURCE --output DESTINATION` copies a resolved package into a new bundle. `DESTINATION/plugin`
points to its complete root. A spec-capable loader can consume that directory directly. Source packages can come from
an existing marketplace checkout, a pinned repository or a local directory; no registry service is required. The builder
checks package identity and filesystem containment. The receiving loader validates its component definitions.

Optional repeated `--target` arguments add harness discovery artifacts. Claude and Codex get native marketplace catalogs;
OpenCode gets native configuration through the pinned public [dotagents CLI](https://github.com/getsentry/dotagents).
Pi gets `.pi/plugins/NAME`, and Hermes gets `.hermes/plugins/NAME`, both pointing to the complete package. There is no
skills-only Pi projection. Authored files are restored after rendering, and authored Claude manifests remain authoritative.

[Pi's Agent Plugins loader](https://github.com/BlockedPath/pi-agent-plugins) and its `pi-mcp-adapter` dependency must be
installed for Pi to load these directories. [Hermes](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins)
requires a version with Agent Plugins support and normal plugin enablement. Distribution does not install loaders or
change their trust decisions. Native discovery catalogs are local installation artifacts, not a private marketplace.

Agent Plugins v1 standardizes skills and MCP. It carries other artifacts in client extensions, whose semantics belong to
their loaders. Delivering an extension preserves it for its intended client; it does not translate arbitrary hooks or
workflows into every other client's runtime. New spec-capable clients can use the same complete `plugin` directory
without adding another artifact adapter.

The Nix entry point is `import ./default.nix { inherit pkgs; }`. Its `package` provides the CLI, and
`buildPlugin { source = pinnedPluginDirectory; }` produces an immutable bundle with all five discovery targets. Set
`targets = [];` for only the complete package. Home Manager installs the builder on Darwin and Linux. Nix owns fetching
and pinning; builds use local inputs. Upstream rendering commands have a 30-second timeout. Outside a sandbox, upstream
may attempt its bounded optional update check, which cannot change the pinned renderer.

The Claude MCP bridge supplies native plugin variables and the portable working directory. OpenCode's launcher places
persistent plugin data under `$XDG_STATE_HOME/agent-plugins/opencode/NAME`, defaulting to `~/.local/state`, independently
of the bundle revision. Generated OpenCode paths bind a bundle to its destination; consume Nix outputs in place.

Existing destinations are refused. Failed builds remove only their new output. Directory symlinks and links outside the
package must be materialized before building. Contained file links are materialized. Upstream warnings are printed and retained in
`dotagents-install.log` or `dotagents-doctor.log`; they do not reject a complete package. The doctor result is advisory; installation process failures still
fail the build. Direct package delivery does not depend on that renderer. Live registration, configuration
merging, enablement, removal and rollback remain owned by harness deployment. Keep credentials out of Nix inputs.

Focused tests and the Nix check verify complete source preservation, opaque extensions, authored manifests, executable
permissions, reproducibility, collision handling and failure cleanup. MCP checks execute the generated commands; native
harness discovery and extension loading require separate runtime verification.
