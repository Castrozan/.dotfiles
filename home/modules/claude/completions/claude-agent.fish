function __claude_agent_directories_with_claude_md
    set --local token (commandline --current-token)
    set --local search_directory (dirname -- $token 2>/dev/null)
    if test -z "$search_directory"
        set search_directory .
    end
    for candidate in $search_directory/*/
        set --local candidate_directory (string trim --right --chars=/ -- $candidate)
        if test -f "$candidate_directory/CLAUDE.md"
            echo $candidate_directory
        end
    end
end

complete --command claude-agent --no-files

complete --command claude-agent --keep-order \
    --arguments '(__claude_agent_directories_with_claude_md)' \
    --description "Project directory (must contain CLAUDE.md)"

complete --command claude-agent --long-option model --require-parameter \
    --arguments 'opus\t"Claude Opus" sonnet\t"Claude Sonnet" haiku\t"Claude Haiku"' \
    --description "Claude model alias"

complete --command claude-agent --long-option name --require-parameter \
    --description "Agent/session name (overrides .pm/agent.json)"

complete --command claude-agent --long-option heartbeat --require-parameter \
    --description "Heartbeat cron expression (overrides .pm/agent.json)"

complete --command claude-agent --long-option no-bootstrap \
    --description "Skip sending the bootstrap prompt"

complete --command claude-agent --long-option keepalive \
    --description "Stay alive while tmux session exists (for systemd)"

complete --command claude-agent --long-option active-hours-start --require-parameter \
    --arguments '(seq 0 23)' \
    --description "Hour (0-23) when agent becomes active"

complete --command claude-agent --long-option active-hours-end --require-parameter \
    --arguments '(seq 0 23)' \
    --description "Hour (0-23) when agent goes dormant"

complete --command claude-agent --short-option h --long-option help \
    --description "Show help message and exit"
