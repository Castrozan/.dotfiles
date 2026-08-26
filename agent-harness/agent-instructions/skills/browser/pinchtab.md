<last_resort_boundary>
Read and use this workflow only after the last-resort eligibility gate in `SKILL.md` passes. This file never authorizes
switching away from Chrome DevTools.
</last_resort_boundary>

<workflow>
PinchTab is a CLI, not an MCP, and drives a separate persistent-profile Chrome. `pinchtab nav` auto-starts its local
server. The declarative config enables its browser capabilities on every host and defaults the shared server to headed.
Work in this order: 1) `pinchtab nav <url>` navigates, with `--new-tab` or `--snap` when needed; 2) `pinchtab snap`
returns refs, which change after navigation or interaction; 3) `pinchtab click <ref>` and
`pinchtab type <ref> <text>` interact; 4) `pinchtab screenshot --output <file>` saves visual evidence while
`pinchtab capture` pairs it with a snapshot; 5) `pinchtab text` extracts text while `pinchtab health` and
`pinchtab tabs` inspect server state. Use `pinchtab help` or a command's `--help` for the changing CLI surface. Switch
the one shared server with `pinchtab-mode headless` or `pinchtab-mode headed`; a mode switch restarts it for every
client, and the next rebuild restores headed mode. Never attempt a second server for another mode because both
instances race the same pidfile.
</workflow>
