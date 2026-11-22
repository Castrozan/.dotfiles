# Topic: target-architecture

Context files: {AVATAR_ROOT}/docs/INVENTORY.md, {AVATAR_ROOT}/docs/PROPOSAL.md, {AVATAR_ROOT}/runtime/README.md, and the
sources under {AVATAR_ROOT}/runtime and {AVATAR_ROOT}/skills.

Design the target as one system: one Cargo workspace, one distributable artifact where achievable, crates as internal
modules and not separately deployed parts. Decide the crate layout and dependency direction (stable core, drivers and
transports at the edge). State plainly what cannot be folded into one binary and how each ships: the three-vrm browser
renderer (compare an embedded webview such as wry or tauri against a bundled or downloaded Chromium, and a pure Rust
renderer), speech and transcription model runtimes (whisper.cpp, ONNX Runtime, sherpa-onnx, Piper: static link versus
sidecar versus downloaded models), platform audio (PipeWire and PulseAudio on Linux, CoreAudio and virtual devices on
macOS, WASAPI on Windows), the virtual camera, and the Discord voice bridge. Name the Rust crates for the control server,
async runtime, serialization, CLI, configuration and tracing, with maintenance evidence for each.
