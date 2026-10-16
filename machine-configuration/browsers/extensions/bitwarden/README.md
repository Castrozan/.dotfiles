# Chromium Bitwarden configuration only

Import `chromium-bitwarden-home-manager.nix` into a Home Manager configuration for an existing, supported Chromium:

```nix
{
  imports = [
    ./machine-configuration/browsers/extensions/bitwarden/chromium-bitwarden-home-manager.nix
  ];
}
```

This module is opt-in; no machine or cloud profile imports it yet. It sets `programs.chromium.enable = true` and
`package = null` and declares only Bitwarden's external-extension metadata. It adds no browser package, executable,
launcher, profile replacement, MIME default, native messaging host, service, custom activation script or browser flags.
A conflicting Chromium package configuration fails evaluation rather than being silently replaced. Existing browser
installation, launch arguments, profile, update policy and platform control remain with their current owner.

## Generated configuration

The pinned Home Manager revision `0d02ec1d0a05f88ef9e74b516842900c41f0f2fe` supports a nullable Chromium package.
Its `modules/programs/chromium.nix` adds `home.packages` only when the resulting package is non-null, but generates the
extension file independently. It rejects command-line arguments when `package = null`.

The only added file is `nngceckbapebfimnlniiiahkandclblb.json`, containing:

```json
{"external_update_url":"https://clients2.google.com/service/update2/crx"}
```

Home Manager places it at these user-owned external-extension locations:

- Linux: `${config.xdg.configHome}/chromium/External Extensions/` (normally `~/.config/chromium/External Extensions/`).
- macOS: `~/Library/Application Support/Chromium/External Extensions/`.

This is a public install/update declaration, not a pinned extension binary. The browser fetches the extension later;
its download size and runtime cost are outside this Nix manifest's closure. The declaration contains no vault credentials,
login state, private session data, unlock policy, autofill settings or security-setting changes.

The ID is the official [Bitwarden Inc. Chrome Web Store listing](https://chromewebstore.google.com/detail/bitwarden-password-manage/nngceckbapebfimnlniiiahkandclblb).
The HTTPS update endpoint follows [Chrome's documented external-extension format](https://developer.chrome.com/docs/extensions/how-to/distribute/install-extensions).
This metadata is not a force-install enterprise policy. Browser confirmation, administrator policy and a previous user
uninstall can affect installation; do not alter those settings or restore a deliberately removed extension automatically.

## Deployment prerequisite and managed-browser boundary

Before any activation, the browser/platform owner must confirm that the actual existing browser is an unbranded Chromium
build that supports per-user external-extension JSON, reads the exact directory above for its launched user/environment,
permits Bitwarden under its extension policy, and supports the normal confirmation/restart workflow. Home Manager must
have an authorized persistent home/configuration location for that same user. A custom `--user-data-dir`, ephemeral
sandbox, managed profile or product name alone does not establish that the browser will read this file.

Proprietary Google Chrome is unsupported by this Home Manager mechanism: the pinned module deliberately removes its
`programs.google-chrome.extensions` option. Do not copy Chromium metadata into Chrome or a platform-managed profile as
a workaround. Windows is outside Home Manager's supported targets. macOS path generation is evaluated, not live-tested.

The managed cloud browser's internal `chrome://extensions` route was denied by its HTTP/HTTPS-only interface. Its profile
and external-extension support remain unverified. This module neither retries that route nor uses filesystem injection,
CDP, an alternate browser, launcher flags or another transport to bypass the restriction. Managed-cloud deployment is
pending a platform-supported extension provisioning/configuration interface and explicit authority to use it.

No real browser installation, profile write, login/unlock or activation is part of this change. Repository integration
keeps the module opt-in; adding a target import and activating it require the target-specific prerequisites above.
Removing the import removes Home Manager's manifest on a later authorized activation; it does not authorize clearing
browser state or manipulating the vault.

## Standalone verification

`__tests__/configurations.nix` evaluates minimal baseline/configured Home Manager configurations with supplied `pkgs`
and `homeManager`. It imports no machine, browser wrapper or platform profile. `__tests__/checks.nix` is discovered by
the repository Nix check loader and covers null package/closure inputs, the single exact manifest, platform/XDG paths,
preserved launcher/environment controls, and package/flag conflicts. Its build check compares the generated home-files
manifest with the official JSON. Build the selected `domain-browser-bitwarden-*` checks without activating a home.

Measure configuration impact by building `baseline.home-files` and `configured.home-files` from the fixture, then compare
`nix path-info --json --recursive` results. The expected delta is one tiny JSON store object plus the changed home-files
tree, with no new browser runtime. Full Home Manager activation has its own existing tooling closure; it is not the
extension's cost. Linux builds and macOS evaluation verify configuration generation only, not live extension acceptance.
