function __claude_complete_no_subcommand
    set --local tokens (commandline --current-process --tokenize --cut-at-cursor)
    set --erase tokens[1]
    set --local subcommands agents auth auto-mode doctor install mcp plugin plugins project setup-token ultrareview update upgrade
    for token in $tokens
        if contains -- $token $subcommands
            return 1
        end
    end
    return 0
end

function __claude_seen_command
    set --local tokens (commandline --current-process --tokenize --cut-at-cursor)
    set --erase tokens[1]
    for token in $tokens
        if contains -- $token $argv
            return 0
        end
    end
    return 1
end

function __claude_in_subcommand_without_nested
    set --local parent $argv[1]
    set --local nested $argv[2..-1]
    if __claude_seen_command $parent
        for nested_command in $nested
            if __claude_seen_command $nested_command
                return 1
            end
        end
        return 0
    end
    return 1
end

complete --command claude --no-files

complete --command claude --condition __claude_complete_no_subcommand --arguments agents --description "Manage background and configured agents"
complete --command claude --condition __claude_complete_no_subcommand --arguments auth --description "Manage authentication"
complete --command claude --condition __claude_complete_no_subcommand --arguments auto-mode --description "Inspect auto mode classifier configuration"
complete --command claude --condition __claude_complete_no_subcommand --arguments doctor --description "Check the health of the Claude Code auto-updater"
complete --command claude --condition __claude_complete_no_subcommand --arguments install --description "Install Claude Code native build"
complete --command claude --condition __claude_complete_no_subcommand --arguments mcp --description "Configure and manage MCP servers"
complete --command claude --condition __claude_complete_no_subcommand --arguments plugin --description "Manage Claude Code plugins"
complete --command claude --condition __claude_complete_no_subcommand --arguments plugins --description "Manage Claude Code plugins (alias)"
complete --command claude --condition __claude_complete_no_subcommand --arguments project --description "Manage Claude Code project state"
complete --command claude --condition __claude_complete_no_subcommand --arguments setup-token --description "Set up a long-lived authentication token"
complete --command claude --condition __claude_complete_no_subcommand --arguments ultrareview --description "Run a cloud-hosted multi-agent code review"
complete --command claude --condition __claude_complete_no_subcommand --arguments update --description "Check for updates and install if available"
complete --command claude --condition __claude_complete_no_subcommand --arguments upgrade --description "Check for updates and install if available (alias)"

complete --command claude --condition __claude_complete_no_subcommand --long-option add-dir --require-parameter --force-files --description "Additional directories to allow tool access to"
complete --command claude --condition __claude_complete_no_subcommand --long-option agent --require-parameter --description "Agent for the current session"
complete --command claude --condition __claude_complete_no_subcommand --long-option agents --require-parameter --description "JSON object defining custom agents"
complete --command claude --condition __claude_complete_no_subcommand --long-option allow-dangerously-skip-permissions --description "Enable bypassing all permission checks as an option"
complete --command claude --condition __claude_complete_no_subcommand --long-option allowedTools --require-parameter --description "Tool names to allow"
complete --command claude --condition __claude_complete_no_subcommand --long-option allowed-tools --require-parameter --description "Tool names to allow"
complete --command claude --condition __claude_complete_no_subcommand --long-option append-system-prompt --require-parameter --description "Append a system prompt to the default"
complete --command claude --condition __claude_complete_no_subcommand --long-option append-system-prompt-file --require-parameter --force-files --description "Append a system prompt loaded from a file"
complete --command claude --condition __claude_complete_no_subcommand --long-option bare --description "Minimal mode: skip hooks, plugins, auto-memory, CLAUDE.md auto-discovery"
complete --command claude --condition __claude_complete_no_subcommand --long-option betas --require-parameter --description "Beta headers to include in API requests"
complete --command claude --condition __claude_complete_no_subcommand --long-option brief --description "Enable SendUserMessage tool for agent-to-user communication"
complete --command claude --condition __claude_complete_no_subcommand --long-option chrome --description "Enable Claude in Chrome integration"
complete --command claude --condition __claude_complete_no_subcommand --short-option c --long-option continue --description "Continue the most recent conversation"
complete --command claude --condition __claude_complete_no_subcommand --long-option dangerously-skip-permissions --description "Bypass all permission checks"
complete --command claude --condition __claude_complete_no_subcommand --short-option d --long-option debug --description "Enable debug mode with optional category filtering"
complete --command claude --condition __claude_complete_no_subcommand --long-option debug-file --require-parameter --force-files --description "Write debug logs to a specific file path"
complete --command claude --condition __claude_complete_no_subcommand --long-option disable-slash-commands --description "Disable all skills"
complete --command claude --condition __claude_complete_no_subcommand --long-option disallowedTools --require-parameter --description "Tool names to deny"
complete --command claude --condition __claude_complete_no_subcommand --long-option disallowed-tools --require-parameter --description "Tool names to deny"
complete --command claude --condition __claude_complete_no_subcommand --long-option effort --require-parameter --exclusive --arguments "low medium high xhigh max" --description "Effort level for the current session"
complete --command claude --condition __claude_complete_no_subcommand --long-option exclude-dynamic-system-prompt-sections --description "Move per-machine sections into the first user message"
complete --command claude --condition __claude_complete_no_subcommand --long-option fallback-model --require-parameter --description "Fallback model when default is overloaded (only with --print)"
complete --command claude --condition __claude_complete_no_subcommand --long-option file --require-parameter --description "File resources to download (file_id:relative_path)"
complete --command claude --condition __claude_complete_no_subcommand --long-option fork-session --description "On resume, create a new session ID instead of reusing the original"
complete --command claude --condition __claude_complete_no_subcommand --long-option from-pr --description "Resume a session linked to a PR by number/URL"
complete --command claude --condition __claude_complete_no_subcommand --short-option h --long-option help --description "Display help"
complete --command claude --condition __claude_complete_no_subcommand --long-option ide --description "Auto-connect to IDE on startup if exactly one valid IDE is available"
complete --command claude --condition __claude_complete_no_subcommand --long-option include-hook-events --description "Include all hook lifecycle events in the output stream"
complete --command claude --condition __claude_complete_no_subcommand --long-option include-partial-messages --description "Include partial message chunks as they arrive"
complete --command claude --condition __claude_complete_no_subcommand --long-option input-format --require-parameter --exclusive --arguments "text stream-json" --description "Input format (only with --print)"
complete --command claude --condition __claude_complete_no_subcommand --long-option json-schema --require-parameter --description "JSON Schema for structured output validation"
complete --command claude --condition __claude_complete_no_subcommand --long-option max-budget-usd --require-parameter --description "Maximum dollar amount to spend on API calls"
complete --command claude --condition __claude_complete_no_subcommand --long-option mcp-config --require-parameter --force-files --description "Load MCP servers from JSON files or strings"
complete --command claude --condition __claude_complete_no_subcommand --long-option mcp-debug --description "[DEPRECATED] Enable MCP debug mode"
complete --command claude --condition __claude_complete_no_subcommand --long-option model --require-parameter --exclusive --arguments "sonnet opus haiku claude-sonnet-4-6 claude-opus-4-7 claude-haiku-4-5-20251001" --description "Model for the current session"
complete --command claude --condition __claude_complete_no_subcommand --short-option n --long-option name --require-parameter --description "Display name for this session"
complete --command claude --condition __claude_complete_no_subcommand --long-option no-chrome --description "Disable Claude in Chrome integration"
complete --command claude --condition __claude_complete_no_subcommand --long-option no-session-persistence --description "Disable session persistence (only with --print)"
complete --command claude --condition __claude_complete_no_subcommand --long-option output-format --require-parameter --exclusive --arguments "text json stream-json" --description "Output format (only with --print)"
complete --command claude --condition __claude_complete_no_subcommand --long-option permission-mode --require-parameter --exclusive --arguments "acceptEdits auto bypassPermissions default dontAsk plan" --description "Permission mode for the session"
complete --command claude --condition __claude_complete_no_subcommand --long-option plugin-dir --require-parameter --force-files --description "Load plugins from a directory for this session"
complete --command claude --condition __claude_complete_no_subcommand --short-option p --long-option print --description "Print response and exit (useful for pipes)"
complete --command claude --condition __claude_complete_no_subcommand --long-option remote-control-session-name-prefix --require-parameter --description "Prefix for auto-generated Remote Control session names"
complete --command claude --condition __claude_complete_no_subcommand --long-option replay-user-messages --description "Re-emit user messages from stdin back on stdout"
complete --command claude --condition __claude_complete_no_subcommand --short-option r --long-option resume --description "Resume a conversation by session ID"
complete --command claude --condition __claude_complete_no_subcommand --long-option session-id --require-parameter --description "Use a specific session ID (must be a valid UUID)"
complete --command claude --condition __claude_complete_no_subcommand --long-option setting-sources --require-parameter --description "Comma-separated setting sources (user, project, local)"
complete --command claude --condition __claude_complete_no_subcommand --long-option settings --require-parameter --force-files --description "Path to a settings JSON file or a JSON string"
complete --command claude --condition __claude_complete_no_subcommand --long-option strict-mcp-config --description "Only use MCP servers from --mcp-config"
complete --command claude --condition __claude_complete_no_subcommand --long-option system-prompt --require-parameter --description "System prompt to use for the session"
complete --command claude --condition __claude_complete_no_subcommand --long-option system-prompt-file --require-parameter --force-files --description "System prompt loaded from a file"
complete --command claude --condition __claude_complete_no_subcommand --long-option tmux --description "Create a tmux session for the worktree (requires --worktree)"
complete --command claude --condition __claude_complete_no_subcommand --long-option tools --require-parameter --description "List of available tools from the built-in set"
complete --command claude --condition __claude_complete_no_subcommand --long-option verbose --description "Override verbose mode setting from config"
complete --command claude --condition __claude_complete_no_subcommand --short-option v --long-option version --description "Output the version number"
complete --command claude --condition __claude_complete_no_subcommand --short-option w --long-option worktree --description "Create a new git worktree for this session"

complete --command claude --condition "__claude_seen_command agents" --long-option setting-sources --require-parameter --description "Comma-separated setting sources (user, project, local)"
complete --command claude --condition "__claude_seen_command agents" --short-option h --long-option help --description "Display help"

complete --command claude --condition "__claude_in_subcommand_without_nested auth login logout status" --arguments login --description "Sign in to your Anthropic account"
complete --command claude --condition "__claude_in_subcommand_without_nested auth login logout status" --arguments logout --description "Log out from your Anthropic account"
complete --command claude --condition "__claude_in_subcommand_without_nested auth login logout status" --arguments status --description "Show authentication status"

complete --command claude --condition "__claude_seen_command auth; and __claude_seen_command login" --long-option claudeai --description "Use Claude subscription (default)"
complete --command claude --condition "__claude_seen_command auth; and __claude_seen_command login" --long-option console --description "Use Anthropic Console (API usage billing)"
complete --command claude --condition "__claude_seen_command auth; and __claude_seen_command login" --long-option email --require-parameter --description "Pre-populate email address on the login page"
complete --command claude --condition "__claude_seen_command auth; and __claude_seen_command login" --long-option sso --description "Force SSO login flow"

complete --command claude --condition "__claude_seen_command auth; and __claude_seen_command status" --long-option json --description "Output as JSON (default)"
complete --command claude --condition "__claude_seen_command auth; and __claude_seen_command status" --long-option text --description "Output as human-readable text"

complete --command claude --condition "__claude_in_subcommand_without_nested auto-mode config critique defaults" --arguments config --description "Print the effective auto mode config as JSON"
complete --command claude --condition "__claude_in_subcommand_without_nested auto-mode config critique defaults" --arguments critique --description "Get AI feedback on your custom auto mode rules"
complete --command claude --condition "__claude_in_subcommand_without_nested auto-mode config critique defaults" --arguments defaults --description "Print the default auto mode environment, allow, and deny rules"

complete --command claude --condition "__claude_seen_command auto-mode; and __claude_seen_command critique" --long-option model --require-parameter --description "Override which model is used"

complete --command claude --condition "__claude_seen_command install" --long-option force --description "Force installation even if already installed"
complete --command claude --condition "__claude_seen_command install" --short-option h --long-option help --description "Display help"

complete --command claude --condition "__claude_seen_command mcp; and not __claude_seen_command marketplace; and __claude_in_subcommand_without_nested mcp add list remove serve get add-from-claude-desktop add-json reset-project-choices help" --arguments add --description "Add an MCP server"
complete --command claude --condition "__claude_seen_command mcp; and not __claude_seen_command marketplace; and __claude_in_subcommand_without_nested mcp add list remove serve get add-from-claude-desktop add-json reset-project-choices help" --arguments add-from-claude-desktop --description "Import MCP servers from Claude Desktop"
complete --command claude --condition "__claude_seen_command mcp; and not __claude_seen_command marketplace; and __claude_in_subcommand_without_nested mcp add list remove serve get add-from-claude-desktop add-json reset-project-choices help" --arguments add-json --description "Add an MCP server (stdio or SSE) with a JSON string"
complete --command claude --condition "__claude_seen_command mcp; and not __claude_seen_command marketplace; and __claude_in_subcommand_without_nested mcp add list remove serve get add-from-claude-desktop add-json reset-project-choices help" --arguments get --description "Get details about an MCP server"
complete --command claude --condition "__claude_seen_command mcp; and not __claude_seen_command marketplace; and __claude_in_subcommand_without_nested mcp add list remove serve get add-from-claude-desktop add-json reset-project-choices help" --arguments list --description "List configured MCP servers"
complete --command claude --condition "__claude_seen_command mcp; and not __claude_seen_command marketplace; and __claude_in_subcommand_without_nested mcp add list remove serve get add-from-claude-desktop add-json reset-project-choices help" --arguments remove --description "Remove an MCP server"
complete --command claude --condition "__claude_seen_command mcp; and not __claude_seen_command marketplace; and __claude_in_subcommand_without_nested mcp add list remove serve get add-from-claude-desktop add-json reset-project-choices help" --arguments reset-project-choices --description "Reset all approved/rejected project-scoped servers"
complete --command claude --condition "__claude_seen_command mcp; and not __claude_seen_command marketplace; and __claude_in_subcommand_without_nested mcp add list remove serve get add-from-claude-desktop add-json reset-project-choices help" --arguments serve --description "Start the Claude Code MCP server"

complete --command claude --condition "__claude_seen_command mcp; and __claude_seen_command add" --short-option t --long-option transport --require-parameter --exclusive --arguments "stdio sse http" --description "Transport type"
complete --command claude --condition "__claude_seen_command mcp; and __claude_seen_command add" --short-option s --long-option scope --require-parameter --exclusive --arguments "local user project" --description "Configuration scope"
complete --command claude --condition "__claude_seen_command mcp; and __claude_seen_command add" --short-option e --long-option env --require-parameter --description "Set environment variables (KEY=value)"
complete --command claude --condition "__claude_seen_command mcp; and __claude_seen_command add" --short-option H --long-option header --require-parameter --description "Set WebSocket headers"
complete --command claude --condition "__claude_seen_command mcp; and __claude_seen_command add" --long-option client-id --require-parameter --description "OAuth client ID for HTTP/SSE servers"
complete --command claude --condition "__claude_seen_command mcp; and __claude_seen_command add" --long-option client-secret --description "Prompt for OAuth client secret"
complete --command claude --condition "__claude_seen_command mcp; and __claude_seen_command add" --long-option callback-port --require-parameter --description "Fixed port for OAuth callback"

complete --command claude --condition "__claude_seen_command mcp; and __claude_seen_command add-from-claude-desktop" --short-option s --long-option scope --require-parameter --exclusive --arguments "local user project" --description "Configuration scope"

complete --command claude --condition "__claude_seen_command mcp; and __claude_seen_command add-json" --short-option s --long-option scope --require-parameter --exclusive --arguments "local user project" --description "Configuration scope"
complete --command claude --condition "__claude_seen_command mcp; and __claude_seen_command add-json" --long-option client-secret --description "Prompt for OAuth client secret"

complete --command claude --condition "__claude_seen_command mcp; and __claude_seen_command remove" --short-option s --long-option scope --require-parameter --exclusive --arguments "local user project" --description "Configuration scope"

complete --command claude --condition "__claude_seen_command mcp; and __claude_seen_command serve" --short-option d --long-option debug --description "Enable debug mode"
complete --command claude --condition "__claude_seen_command mcp; and __claude_seen_command serve" --long-option verbose --description "Override verbose mode setting from config"

complete --command claude --condition "__claude_seen_command plugin plugins; and not __claude_seen_command marketplace; and __claude_in_subcommand_without_nested plugin install i enable disable uninstall remove update tag validate list marketplace prune autoremove help" --arguments install --description "Install a plugin from available marketplaces"
complete --command claude --condition "__claude_seen_command plugin plugins; and not __claude_seen_command marketplace; and __claude_in_subcommand_without_nested plugin install i enable disable uninstall remove update tag validate list marketplace prune autoremove help" --arguments enable --description "Enable a disabled plugin"
complete --command claude --condition "__claude_seen_command plugin plugins; and not __claude_seen_command marketplace; and __claude_in_subcommand_without_nested plugin install i enable disable uninstall remove update tag validate list marketplace prune autoremove help" --arguments disable --description "Disable an enabled plugin"
complete --command claude --condition "__claude_seen_command plugin plugins; and not __claude_seen_command marketplace; and __claude_in_subcommand_without_nested plugin install i enable disable uninstall remove update tag validate list marketplace prune autoremove help" --arguments uninstall --description "Uninstall an installed plugin"
complete --command claude --condition "__claude_seen_command plugin plugins; and not __claude_seen_command marketplace; and __claude_in_subcommand_without_nested plugin install i enable disable uninstall remove update tag validate list marketplace prune autoremove help" --arguments update --description "Update a plugin to the latest version"
complete --command claude --condition "__claude_seen_command plugin plugins; and not __claude_seen_command marketplace; and __claude_in_subcommand_without_nested plugin install i enable disable uninstall remove update tag validate list marketplace prune autoremove help" --arguments tag --description "Create a release git tag for a plugin"
complete --command claude --condition "__claude_seen_command plugin plugins; and not __claude_seen_command marketplace; and __claude_in_subcommand_without_nested plugin install i enable disable uninstall remove update tag validate list marketplace prune autoremove help" --arguments validate --description "Validate a plugin or marketplace manifest"
complete --command claude --condition "__claude_seen_command plugin plugins; and not __claude_seen_command marketplace; and __claude_in_subcommand_without_nested plugin install i enable disable uninstall remove update tag validate list marketplace prune autoremove help" --arguments list --description "List installed plugins"
complete --command claude --condition "__claude_seen_command plugin plugins; and not __claude_seen_command marketplace; and __claude_in_subcommand_without_nested plugin install i enable disable uninstall remove update tag validate list marketplace prune autoremove help" --arguments marketplace --description "Manage Claude Code marketplaces"
complete --command claude --condition "__claude_seen_command plugin plugins; and not __claude_seen_command marketplace; and __claude_in_subcommand_without_nested plugin install i enable disable uninstall remove update tag validate list marketplace prune autoremove help" --arguments prune --description "Remove auto-installed dependencies that are no longer needed"

complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command install i" --short-option s --long-option scope --require-parameter --exclusive --arguments "user project local" --description "Installation scope"

complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command enable" --short-option s --long-option scope --require-parameter --exclusive --arguments "user project local" --description "Installation scope"

complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command disable" --short-option a --long-option all --description "Disable all enabled plugins"
complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command disable" --short-option s --long-option scope --require-parameter --exclusive --arguments "user project local" --description "Installation scope"

complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command uninstall remove" --long-option keep-data --description "Preserve the plugin's persistent data directory"
complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command uninstall remove" --long-option prune --description "Also remove auto-installed dependencies"
complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command uninstall remove" --short-option s --long-option scope --require-parameter --exclusive --arguments "user project local" --description "Uninstall from scope"
complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command uninstall remove" --short-option y --long-option yes --description "Skip the --prune confirmation prompt"

complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command update; and not __claude_seen_command marketplace" --short-option s --long-option scope --require-parameter --exclusive --arguments "user project local managed" --description "Installation scope"

complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command tag" --long-option dry-run --description "Print what would be tagged without creating it"
complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command tag" --short-option f --long-option force --description "Skip dirty-working-tree and tag-already-exists checks"
complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command tag" --short-option m --long-option message --require-parameter --description "Tag annotation message (use %s for the version)"
complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command tag" --long-option push --description "Push the tag to --remote after creating it"
complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command tag" --long-option remote --require-parameter --description "Remote to push to with --push (default: origin)"

complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command list; and not __claude_seen_command marketplace" --long-option available --description "Include available plugins from marketplaces (requires --json)"
complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command list; and not __claude_seen_command marketplace" --long-option json --description "Output as JSON"

complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command prune autoremove" --long-option dry-run --description "List what would be removed without removing"
complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command prune autoremove" --short-option s --long-option scope --require-parameter --exclusive --arguments "user project local" --description "Prune at scope"
complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command prune autoremove" --short-option y --long-option yes --description "Skip the confirmation prompt"

complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command marketplace; and __claude_in_subcommand_without_nested marketplace add list remove rm update help" --arguments add --description "Add a marketplace from a URL, path, or GitHub repo"
complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command marketplace; and __claude_in_subcommand_without_nested marketplace add list remove rm update help" --arguments list --description "List all configured marketplaces"
complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command marketplace; and __claude_in_subcommand_without_nested marketplace add list remove rm update help" --arguments remove --description "Remove a configured marketplace"
complete --command claude --condition "__claude_seen_command plugin plugins; and __claude_seen_command marketplace; and __claude_in_subcommand_without_nested marketplace add list remove rm update help" --arguments update --description "Update marketplaces from their source"

complete --command claude --condition "__claude_seen_command marketplace; and __claude_seen_command add" --long-option scope --require-parameter --exclusive --arguments "user project local" --description "Where to declare the marketplace"
complete --command claude --condition "__claude_seen_command marketplace; and __claude_seen_command add" --long-option sparse --require-parameter --description "Limit checkout to specific directories via git sparse-checkout"

complete --command claude --condition "__claude_seen_command marketplace; and __claude_seen_command list" --long-option json --description "Output as JSON"

complete --command claude --condition "__claude_in_subcommand_without_nested project purge help" --arguments purge --description "Delete all Claude Code state for a project"

complete --command claude --condition "__claude_seen_command project; and __claude_seen_command purge" --long-option all --description "Purge state for every project"
complete --command claude --condition "__claude_seen_command project; and __claude_seen_command purge" --long-option dry-run --description "List what would be deleted without deleting"
complete --command claude --condition "__claude_seen_command project; and __claude_seen_command purge" --short-option i --long-option interactive --description "Prompt for each item before deleting"
complete --command claude --condition "__claude_seen_command project; and __claude_seen_command purge" --short-option y --long-option yes --description "Skip confirmation prompt"

complete --command claude --condition "__claude_seen_command ultrareview" --long-option json --description "Print the raw bugs.json payload instead of formatted findings"
complete --command claude --condition "__claude_seen_command ultrareview" --long-option timeout --require-parameter --description "Maximum minutes to wait for the review to finish"
