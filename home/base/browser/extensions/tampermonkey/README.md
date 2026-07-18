# Tampermonkey userscripts

Version-controlled backup of the userscripts imported into Tampermonkey by hand. This directory is the source of truth: edit the `.user.js` here, then reinstall it in the browser.

No Nix module references these files, so they are not part of any derivation. Running `rebuild` or `tests/run.sh` does nothing for a change to a script here. Installing and updating happens in the browser, never through the system build.
