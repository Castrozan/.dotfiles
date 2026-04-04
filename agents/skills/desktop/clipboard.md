<execution>
Run `scripts/clipboard.sh` with subcommand: `read`, `write`, or `watch`. Pass `--type MIME` for typed content. Write accepts text as argument or via stdin.
</execution>

<pitfalls>
Wayland-only — requires socket access. Image reads save to /tmp and print the path (not raw binary). Empty clipboard returns empty string, not an error. The `watch` subcommand runs until interrupted — don't use in unattended one-shot automation.
</pitfalls>
