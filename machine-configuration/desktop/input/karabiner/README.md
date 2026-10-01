Karabiner-Elements is installed through Homebrew. The Nix-owned activation checks the installed application's full version before changing the system and upgrades only the Karabiner cask when it falls below the declared minimum. Once the minimum is satisfied, activation performs no Homebrew upgrade or network request for this check. Installation failure or a version that remains too old aborts activation.

The minimum includes the upstream fix for [shared-secret desynchronization][shared-secret-fix], which could freeze application detection while ordinary IPC probes continued to succeed. This failure disabled browser-specific remaps without removing their configuration. Homebrew's normal `--no-upgrade` activation alone does not keep an already-installed cask above that minimum.

Rules are generated from Nix and copied to `~/.config/karabiner/karabiner.json`; [Karabiner does not reliably observe changes through a symlink][config-file-path]. A changed configuration restarts the core-service agent and console-user-server app. Application-focus guards remain default-deny while Hammerspoon reasserts the active application after startup. Karabiner's vendor-managed services own keyboard capture; legacy nix-darwin service registrations are removed to avoid competing installations.

The existing restart-on-wake daemon remains the recovery fallback for failed IPC probes and missing processes. Its periodic safety check leaves healthy services running. `karabiner-status` reports the current probe snapshot. This recovery mechanism cannot prove that application-specific remapping works; verify those shortcuts in the target application.

The workspace switcher's Cmd+Tab rule uses [`to.send_user_command`][send-user-command] to reach its existing UNIX datagram socket without launching a shell on each keypress. Other rules use `shell_command` for application-launch and Hammerspoon operations.

[shared-secret-fix]: https://github.com/pqrs-org/Karabiner-Elements/issues/4470#issuecomment-4970021974
[config-file-path]: https://karabiner-elements.pqrs.org/docs/manual/misc/configuration-file-path/
[send-user-command]: https://karabiner-elements.pqrs.org/docs/json/complex-modifications-manipulator-definition/to/send-user-command/
