### Housekeeping slice

$INPUTS.task

An earlier reader of this slice reported the findings serialized on the next line; an empty list means none.
$INPUTS.earlier_findings

The slice artifact is the file named on the next line.
$INPUTS.slice_path

It holds every file of the slice under a "=== path" header, each line prefixed with its line number inside that file.
Read the whole artifact, in chunks when it is long, and report each finding with the file path from its header and the
line number printed beside it. Read only; change no file.

### Sweep dimensions

Apply all seven dimensions in one pass: 1) TODO, FIXME, WIP, XXX, or HACK markers and commented-out code, excluding
shebangs, load-bearing expressions, and intentional backlog; 2) unused scripts, files, and broken symlinks, proving
absence through imports, globs, filesets, generators, runtime discovery, and PATH lookup; 3) stale, contradictory, or
duplicated policy and pointers across core, project context, skills, agents, hooks, evals, and docs;

4\) long scripts embedded in nix, compatibility shims, aliases, re-exports, bash used for stateful logic, and unguarded
platform-specific configuration; 5) committed private submodule gitlinks that point to unpushed commits, orphaned agent
sessions, settings seed ownership gaps, and flake evaluations that omit required submodules; 6) scripts,
behavior-bearing modules, or recent bug fixes without focused regression coverage, excluding declarative configuration
already proven by rebuild;

7\) real defects: inverted or off-by-one comparisons, wrong boolean operators, dropped negations, wrong defaults or
constants, and broken empty-input handling.

### Coverage exclusions

Report only standing rot that no existing check catches. Skip nix idiom, dead bindings, and nix formatting owned by
statix, deadnix, and nixfmt. Skip line-count violations, code formatting, hardcoded home paths, identifying names,
broken evaluation symlinks, instruction structure, prohibited blanket staging, and anything a repository check or the
pre-push change-review procedure already owns. Skip pure preference.

Try to refute each concern before returning it. Keep each detail under 60 words and rate your confidence from 1 to 5.
