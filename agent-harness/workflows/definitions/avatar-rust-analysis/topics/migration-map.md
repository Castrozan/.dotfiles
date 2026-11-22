# Topic: migration-map

Context files: {AVATAR_ROOT}/docs/INVENTORY.md, {AVATAR_ROOT}/docs/PROPOSAL.md, {AVATAR_ROOT}/docs/CUTOVER.md,
{AVATAR_ROOT}/runtime/README.md, the tests under {AVATAR_ROOT}/runtime/__tests__ and {AVATAR_ROOT}/skills.

Map every component and area in INVENTORY.md section 1 (each row of both tables) to its Rust home: crate and module,
or deleted with a reason, or kept outside Rust with a reason. Order the rewrite as thin end-to-end slices, each leaving a
working system, and name the first slice with its acceptance test. Decide how behaviour is carried over: which of the
existing pytest and node tests become the contract (read them, count them per area), which become golden or recorded
fixtures, and how the Python and Rust versions run side by side and are compared during the transition (shadow mode,
record and replay of audio and control messages, differential tests, a feature flag per slice). Do not run
avatar-talk, avatar-command or discord-voice and do not restart any service; read files only.
