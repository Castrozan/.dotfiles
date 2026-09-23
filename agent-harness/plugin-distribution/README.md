# Plugin distribution prototype

This boundary turns a resolved [Agent Plugins v1 package](https://agent-plugins.org/specification) into native harness
artifacts. It uses the public [dotagents CLI](https://github.com/getsentry/dotagents) as its adapter backend, pinned with
its dependencies in the npm lockfile. It does not depend on Claude's installed cache or require a hosted marketplace.

`agent-plugin-build SOURCE --output DESTINATION --target claude --target codex --target opencode` builds one package
into a new directory. The source must contain the portable root `plugin.json`. Select the package directory from an
existing marketplace checkout, a pinned repository, or a local source before building. Existing destinations are refused;
a failed adapter run removes only the new output. Each upstream command has a 30-second timeout.

The Nix entry point is `import ./default.nix { inherit pkgs; }`. Its `package` provides the CLI; its
`buildPlugin { source = pinnedPluginDirectory; targets = [ "claude" "codex" "opencode" ]; }` produces an immutable
derivation. Home Manager installs the builder on Darwin and Linux. Fetching and pinning sources remain Nix's responsibility;
the build resolves local inputs without requiring network access. The upstream CLI may attempt its bounded optional
update check outside a sandbox; that check cannot change the pinned renderer.

The prototype covers skills, their references and scripts, and stateless MCP configurations for Claude, Codex and
OpenCode. Pi accepts skill-only packages. Required native extensions, persistent instructions, hooks, commands, agents,
workflows and unsupported targets fail explicitly. Directory symlinks and links outside the package must be materialized
before building. Upstream component warnings are fatal instead of silently dropping functionality.

Generated marketplace catalogs are native discovery artifacts. They do not create a registry service. The build output
is tied to its destination because OpenCode's configuration contains absolute paths; consume a Nix store artifact in
place rather than relocating it. Plugin source packages remain portable.

The extraction boundary is generation, before installation. Live configuration merging, registration, ownership-aware
updates, removal and rollback still belong to the existing harness deployment modules. OpenCode's generated plugin-data
directory is inside the output, so writable MCP state needs a separate deployment adapter; explicit `PLUGIN_DATA` use
is rejected. Credentials must remain runtime references and must never be embedded in an input sent to the Nix store.

The focused Python tests cover input rejection and output ownership. The Nix check builds through the real upstream
CLI, compares repeated output, verifies bundled references, exercises failure cleanup, and calls the packaged MCP server
through each generated command. These checks establish artifact and protocol behavior; native harness discovery is a
separate runtime verification.
