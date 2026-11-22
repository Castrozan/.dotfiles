# Topic: reference-repositories

The avatar is a real-time voice system (listening, transcription, turn detection, speech, a three-vrm browser renderer,
a control server, wake words, call audio) now written in Python and JavaScript, to be rewritten in Rust as one system.
Context files: {AVATAR_ROOT}/docs/INVENTORY.md, {AVATAR_ROOT}/docs/PROPOSAL.md, {AVATAR_ROOT}/runtime/README.md.

Settle which existing Rust repositories are the references for repository structure and engineering practice, chosen by
evidence: maintenance, test layout, CI, release engineering, cross-platform distribution. Consider at least ripgrep, uv,
ruff, helix, nushell, wezterm, tauri, zed, deno, cargo itself and rust-analyzer, plus three to five Rust audio, speech or
real-time projects of your own finding (for example crates around cpal, whisper-rs, ort, sherpa-onnx, livekit). For each
kept reference name exactly what to adopt (workspace layout, lint table, CI matrix, release pipeline, test strategy) with
the file path in that repository. Measure with `gh api` (last push, release cadence, workflow files). Finish with the
ranked list of at most six references and what each contributes.
