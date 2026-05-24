for secretFile in "$HOME/.secrets/metabase-api-key" "$HOME/.secrets/work-email" "$HOME/.secrets/work-password" "$HOME/.secrets/elastic-password" "$HOME/.secrets/grafana-password" "$HOME/.secrets/jira-token" "$HOME/.secrets/wiki-token"
    if test -f "$secretFile"
        set -l secretFileName (basename "$secretFile")
        set -l environmentVariableName (string upper (string replace -a '-' '_' "$secretFileName"))
        set -gx $environmentVariableName (cat "$secretFile" 2>/dev/null)
    end
end
