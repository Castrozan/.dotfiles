<rebuild>
Rebuild is sudoless: a NOPASSWD sudoers rule covers it (blanket on NixOS, command-scoped to the nix commands on darwin), so the `rebuild` command never prompts for a password. A bare `sudo -n true` probe can still fail on darwin because the rule is command-scoped, not blanket - do not conclude from that probe that the rebuild needs a password. Run `rebuild` yourself, wait for it to finish, and report the result; never defer it to the user or hand back a command for the user to type.
</rebuild>
