# Tampermonkey userscripts

Loose copies of userscripts kept here in the repo, nothing more. This is not a backup: the authoritative copies and their real backups live in Tampermonkey itself, synced to Google Drive. Editing here is just a convenience, install and persist through the extension.

No Nix module references these files, so a `rebuild` or `repository/verification/run.sh` run does nothing for a change to a script here.

Build the YouTube script before importing it into Tampermonkey:

```sh
python3.12 machine-configuration/browsers/extensions/tampermonkey/youtube-theater-focus/build_userscript.py > /tmp/youtube-theater-focus.user.js
```

The output contains the playback guard and theater layout in one document-start userscript. Install that generated
file through the extension.
