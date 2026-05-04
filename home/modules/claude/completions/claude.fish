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

function __claude_no_subcommand_yet
    set --local subcommands agents auth auto-mode doctor install mcp plugin plugins project setup-token ultrareview update upgrade
    not __claude_seen_command $subcommands
end

function __claude_subcommand_pending
    set --local parent $argv[1]
    set --local known_nested $argv[2..-1]
    __claude_seen_command $parent
    and not __claude_seen_command $known_nested
end

function __claude_register_subcommand_list
    set --local condition $argv[1]
    set --erase argv[1]
    set --local index 1
    while test $index -le (count $argv)
        complete --command claude --condition "$condition" --arguments $argv[$index] --description $argv[(math "$index + 1")]
        set index (math "$index + 2")
    end
end

complete --command claude --no-files

set --local at_root __claude_no_subcommand_yet

__claude_register_subcommand_list $at_root \
    agents      "Manage background and configured agents" \
    auth        "Manage authentication" \
    auto-mode   "Inspect auto mode classifier configuration" \
    doctor      "Check the health of the Claude Code auto-updater" \
    install     "Install Claude Code native build" \
    mcp         "Configure and manage MCP servers" \
    plugin      "Manage Claude Code plugins" \
    plugins     "Manage Claude Code plugins (alias)" \
    project     "Manage Claude Code project state" \
    setup-token "Set up a long-lived authentication token" \
    ultrareview "Run a cloud-hosted multi-agent code review" \
    update      "Check for updates and install if available" \
    upgrade     "Check for updates and install if available (alias)"

complete -c claude -n $at_root -l add-dir -r -F -d "Additional directories to allow tool access to"
complete -c claude -n $at_root -l agent -r -d "Agent for the current session"
complete -c claude -n $at_root -l agents -r -d "JSON object defining custom agents"
complete -c claude -n $at_root -l allow-dangerously-skip-permissions -d "Enable bypassing all permission checks as an option"
complete -c claude -n $at_root -l allowedTools -r -d "Tool names to allow"
complete -c claude -n $at_root -l allowed-tools -r -d "Tool names to allow"
complete -c claude -n $at_root -l append-system-prompt -r -d "Append a system prompt to the default"
complete -c claude -n $at_root -l append-system-prompt-file -r -F -d "Append a system prompt loaded from a file"
complete -c claude -n $at_root -l bare -d "Minimal mode: skip hooks, plugins, auto-memory, CLAUDE.md auto-discovery"
complete -c claude -n $at_root -l betas -r -d "Beta headers to include in API requests"
complete -c claude -n $at_root -l brief -d "Enable SendUserMessage tool for agent-to-user communication"
complete -c claude -n $at_root -l chrome -d "Enable Claude in Chrome integration"
complete -c claude -n $at_root -s c -l continue -d "Continue the most recent conversation"
complete -c claude -n $at_root -l dangerously-skip-permissions -d "Bypass all permission checks"
complete -c claude -n $at_root -s d -l debug -d "Enable debug mode with optional category filtering"
complete -c claude -n $at_root -l debug-file -r -F -d "Write debug logs to a specific file path"
complete -c claude -n $at_root -l disable-slash-commands -d "Disable all skills"
complete -c claude -n $at_root -l disallowedTools -r -d "Tool names to deny"
complete -c claude -n $at_root -l disallowed-tools -r -d "Tool names to deny"
complete -c claude -n $at_root -l effort -x -a "low medium high xhigh max" -d "Effort level for the current session"
complete -c claude -n $at_root -l exclude-dynamic-system-prompt-sections -d "Move per-machine sections into the first user message"
complete -c claude -n $at_root -l fallback-model -r -d "Fallback model when default is overloaded (only with --print)"
complete -c claude -n $at_root -l file -r -d "File resources to download (file_id:relative_path)"
complete -c claude -n $at_root -l fork-session -d "On resume, create a new session ID instead of reusing the original"
complete -c claude -n $at_root -l from-pr -d "Resume a session linked to a PR by number/URL"
complete -c claude -n $at_root -s h -l help -d "Display help"
complete -c claude -n $at_root -l ide -d "Auto-connect to IDE on startup if exactly one valid IDE is available"
complete -c claude -n $at_root -l include-hook-events -d "Include all hook lifecycle events in the output stream"
complete -c claude -n $at_root -l include-partial-messages -d "Include partial message chunks as they arrive"
complete -c claude -n $at_root -l input-format -x -a "text stream-json" -d "Input format (only with --print)"
complete -c claude -n $at_root -l json-schema -r -d "JSON Schema for structured output validation"
complete -c claude -n $at_root -l max-budget-usd -r -d "Maximum dollar amount to spend on API calls"
complete -c claude -n $at_root -l mcp-config -r -F -d "Load MCP servers from JSON files or strings"
complete -c claude -n $at_root -l mcp-debug -d "[DEPRECATED] Enable MCP debug mode"
complete -c claude -n $at_root -l model -x -a "sonnet opus haiku claude-sonnet-4-6 claude-opus-4-7 claude-haiku-4-5-20251001" -d "Model for the current session"
complete -c claude -n $at_root -s n -l name -r -d "Display name for this session"
complete -c claude -n $at_root -l no-chrome -d "Disable Claude in Chrome integration"
complete -c claude -n $at_root -l no-session-persistence -d "Disable session persistence (only with --print)"
complete -c claude -n $at_root -l output-format -x -a "text json stream-json" -d "Output format (only with --print)"
complete -c claude -n $at_root -l permission-mode -x -a "acceptEdits auto bypassPermissions default dontAsk plan" -d "Permission mode for the session"
complete -c claude -n $at_root -l plugin-dir -r -F -d "Load plugins from a directory for this session"
complete -c claude -n $at_root -s p -l print -d "Print response and exit (useful for pipes)"
complete -c claude -n $at_root -l remote-control-session-name-prefix -r -d "Prefix for auto-generated Remote Control session names"
complete -c claude -n $at_root -l replay-user-messages -d "Re-emit user messages from stdin back on stdout"
complete -c claude -n $at_root -s r -l resume -d "Resume a conversation by session ID"
complete -c claude -n $at_root -l session-id -r -d "Use a specific session ID (must be a valid UUID)"
complete -c claude -n $at_root -l setting-sources -r -d "Comma-separated setting sources (user, project, local)"
complete -c claude -n $at_root -l settings -r -F -d "Path to a settings JSON file or a JSON string"
complete -c claude -n $at_root -l strict-mcp-config -d "Only use MCP servers from --mcp-config"
complete -c claude -n $at_root -l system-prompt -r -d "System prompt to use for the session"
complete -c claude -n $at_root -l system-prompt-file -r -F -d "System prompt loaded from a file"
complete -c claude -n $at_root -l tmux -d "Create a tmux session for the worktree (requires --worktree)"
complete -c claude -n $at_root -l tools -r -d "List of available tools from the built-in set"
complete -c claude -n $at_root -l verbose -d "Override verbose mode setting from config"
complete -c claude -n $at_root -s v -l version -d "Output the version number"
complete -c claude -n $at_root -s w -l worktree -d "Create a new git worktree for this session"

set --local at_agents "__claude_seen_command agents"

complete -c claude -n $at_agents -l setting-sources -r -d "Comma-separated setting sources (user, project, local)"
complete -c claude -n $at_agents -s h -l help -d "Display help"

set --local at_auth_root "__claude_subcommand_pending auth login logout status help"

__claude_register_subcommand_list $at_auth_root \
    login  "Sign in to your Anthropic account" \
    logout "Log out from your Anthropic account" \
    status "Show authentication status"

set --local at_auth_login "__claude_seen_command auth; and __claude_seen_command login"

complete -c claude -n $at_auth_login -l claudeai -d "Use Claude subscription (default)"
complete -c claude -n $at_auth_login -l console -d "Use Anthropic Console (API usage billing)"
complete -c claude -n $at_auth_login -l email -r -d "Pre-populate email address on the login page"
complete -c claude -n $at_auth_login -l sso -d "Force SSO login flow"

set --local at_auth_status "__claude_seen_command auth; and __claude_seen_command status"

complete -c claude -n $at_auth_status -l json -d "Output as JSON (default)"
complete -c claude -n $at_auth_status -l text -d "Output as human-readable text"

set --local at_auto_mode_root "__claude_subcommand_pending auto-mode config critique defaults help"

__claude_register_subcommand_list $at_auto_mode_root \
    config   "Print the effective auto mode config as JSON" \
    critique "Get AI feedback on your custom auto mode rules" \
    defaults "Print the default auto mode environment, allow, and deny rules"

set --local at_auto_mode_critique "__claude_seen_command auto-mode; and __claude_seen_command critique"

complete -c claude -n $at_auto_mode_critique -l model -r -d "Override which model is used"

set --local at_install "__claude_seen_command install"

complete -c claude -n $at_install -l force -d "Force installation even if already installed"
complete -c claude -n $at_install -s h -l help -d "Display help"

set --local at_mcp_root "not __claude_seen_command marketplace; and __claude_subcommand_pending mcp add add-from-claude-desktop add-json get list remove reset-project-choices serve help"

__claude_register_subcommand_list $at_mcp_root \
    add                     "Add an MCP server" \
    add-from-claude-desktop "Import MCP servers from Claude Desktop" \
    add-json                "Add an MCP server (stdio or SSE) with a JSON string" \
    get                     "Get details about an MCP server" \
    list                    "List configured MCP servers" \
    remove                  "Remove an MCP server" \
    reset-project-choices   "Reset all approved/rejected project-scoped servers" \
    serve                   "Start the Claude Code MCP server"

set --local at_mcp_add "__claude_seen_command mcp; and __claude_seen_command add"

complete -c claude -n $at_mcp_add -s t -l transport -x -a "stdio sse http" -d "Transport type"
complete -c claude -n $at_mcp_add -s s -l scope -x -a "local user project" -d "Configuration scope"
complete -c claude -n $at_mcp_add -s e -l env -r -d "Set environment variables (KEY=value)"
complete -c claude -n $at_mcp_add -s H -l header -r -d "Set WebSocket headers"
complete -c claude -n $at_mcp_add -l client-id -r -d "OAuth client ID for HTTP/SSE servers"
complete -c claude -n $at_mcp_add -l client-secret -d "Prompt for OAuth client secret"
complete -c claude -n $at_mcp_add -l callback-port -r -d "Fixed port for OAuth callback"

set --local at_mcp_add_from_claude_desktop "__claude_seen_command mcp; and __claude_seen_command add-from-claude-desktop"

complete -c claude -n $at_mcp_add_from_claude_desktop -s s -l scope -x -a "local user project" -d "Configuration scope"

set --local at_mcp_add_json "__claude_seen_command mcp; and __claude_seen_command add-json"

complete -c claude -n $at_mcp_add_json -s s -l scope -x -a "local user project" -d "Configuration scope"
complete -c claude -n $at_mcp_add_json -l client-secret -d "Prompt for OAuth client secret"

set --local at_mcp_remove "__claude_seen_command mcp; and __claude_seen_command remove; and not __claude_seen_command marketplace"

complete -c claude -n $at_mcp_remove -s s -l scope -x -a "local user project" -d "Configuration scope"

set --local at_mcp_serve "__claude_seen_command mcp; and __claude_seen_command serve"

complete -c claude -n $at_mcp_serve -s d -l debug -d "Enable debug mode"
complete -c claude -n $at_mcp_serve -l verbose -d "Override verbose mode setting from config"

set --local at_plugin_root "not __claude_seen_command marketplace; and __claude_subcommand_pending plugin install i enable disable uninstall remove update tag validate list marketplace prune autoremove help"
set --local at_plugins_root "not __claude_seen_command marketplace; and __claude_subcommand_pending plugins install i enable disable uninstall remove update tag validate list marketplace prune autoremove help"

for plugin_root_condition in $at_plugin_root $at_plugins_root
    __claude_register_subcommand_list $plugin_root_condition \
        install     "Install a plugin from available marketplaces" \
        enable      "Enable a disabled plugin" \
        disable     "Disable an enabled plugin" \
        uninstall   "Uninstall an installed plugin" \
        update      "Update a plugin to the latest version" \
        tag         "Create a release git tag for a plugin" \
        validate    "Validate a plugin or marketplace manifest" \
        list        "List installed plugins" \
        marketplace "Manage Claude Code marketplaces" \
        prune       "Remove auto-installed dependencies that are no longer needed"
end

set --local at_plugin_either "__claude_seen_command plugin plugins"

set --local at_plugin_install "$at_plugin_either; and __claude_seen_command install i"

complete -c claude -n "$at_plugin_install" -s s -l scope -x -a "user project local" -d "Installation scope"

set --local at_plugin_enable "$at_plugin_either; and __claude_seen_command enable"

complete -c claude -n "$at_plugin_enable" -s s -l scope -x -a "user project local" -d "Installation scope"

set --local at_plugin_disable "$at_plugin_either; and __claude_seen_command disable"

complete -c claude -n "$at_plugin_disable" -s a -l all -d "Disable all enabled plugins"
complete -c claude -n "$at_plugin_disable" -s s -l scope -x -a "user project local" -d "Installation scope"

set --local at_plugin_uninstall "$at_plugin_either; and __claude_seen_command uninstall remove"

complete -c claude -n "$at_plugin_uninstall" -l keep-data -d "Preserve the plugin's persistent data directory"
complete -c claude -n "$at_plugin_uninstall" -l prune -d "Also remove auto-installed dependencies"
complete -c claude -n "$at_plugin_uninstall" -s s -l scope -x -a "user project local" -d "Uninstall from scope"
complete -c claude -n "$at_plugin_uninstall" -s y -l yes -d "Skip the --prune confirmation prompt"

set --local at_plugin_update "$at_plugin_either; and __claude_seen_command update; and not __claude_seen_command marketplace"

complete -c claude -n "$at_plugin_update" -s s -l scope -x -a "user project local managed" -d "Installation scope"

set --local at_plugin_tag "$at_plugin_either; and __claude_seen_command tag"

complete -c claude -n "$at_plugin_tag" -l dry-run -d "Print what would be tagged without creating it"
complete -c claude -n "$at_plugin_tag" -s f -l force -d "Skip dirty-working-tree and tag-already-exists checks"
complete -c claude -n "$at_plugin_tag" -s m -l message -r -d "Tag annotation message (use %s for the version)"
complete -c claude -n "$at_plugin_tag" -l push -d "Push the tag to --remote after creating it"
complete -c claude -n "$at_plugin_tag" -l remote -r -d "Remote to push to with --push (default: origin)"

set --local at_plugin_list "$at_plugin_either; and __claude_seen_command list; and not __claude_seen_command marketplace"

complete -c claude -n "$at_plugin_list" -l available -d "Include available plugins from marketplaces (requires --json)"
complete -c claude -n "$at_plugin_list" -l json -d "Output as JSON"

set --local at_plugin_prune "$at_plugin_either; and __claude_seen_command prune autoremove"

complete -c claude -n "$at_plugin_prune" -l dry-run -d "List what would be removed without removing"
complete -c claude -n "$at_plugin_prune" -s s -l scope -x -a "user project local" -d "Prune at scope"
complete -c claude -n "$at_plugin_prune" -s y -l yes -d "Skip the confirmation prompt"

set --local at_marketplace_root "$at_plugin_either; and __claude_subcommand_pending marketplace add list remove rm update help"

__claude_register_subcommand_list $at_marketplace_root \
    add    "Add a marketplace from a URL, path, or GitHub repo" \
    list   "List all configured marketplaces" \
    remove "Remove a configured marketplace" \
    update "Update marketplaces from their source"

set --local at_marketplace_add "__claude_seen_command marketplace; and __claude_seen_command add"

complete -c claude -n "$at_marketplace_add" -l scope -x -a "user project local" -d "Where to declare the marketplace"
complete -c claude -n "$at_marketplace_add" -l sparse -r -d "Limit checkout to specific directories via git sparse-checkout"

set --local at_marketplace_list "__claude_seen_command marketplace; and __claude_seen_command list"

complete -c claude -n "$at_marketplace_list" -l json -d "Output as JSON"

set --local at_project_root "__claude_subcommand_pending project purge help"

__claude_register_subcommand_list $at_project_root \
    purge "Delete all Claude Code state for a project"

set --local at_project_purge "__claude_seen_command project; and __claude_seen_command purge"

complete -c claude -n "$at_project_purge" -l all -d "Purge state for every project"
complete -c claude -n "$at_project_purge" -l dry-run -d "List what would be deleted without deleting"
complete -c claude -n "$at_project_purge" -s i -l interactive -d "Prompt for each item before deleting"
complete -c claude -n "$at_project_purge" -s y -l yes -d "Skip confirmation prompt"

set --local at_ultrareview "__claude_seen_command ultrareview"

complete -c claude -n $at_ultrareview -l json -d "Print the raw bugs.json payload instead of formatted findings"
complete -c claude -n $at_ultrareview -l timeout -r -d "Maximum minutes to wait for the review to finish"
