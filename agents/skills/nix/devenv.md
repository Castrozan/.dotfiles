<entering>
devenv shell activates the environment interactively. devenv shell -- command runs a single command then exits. Prefer the latter for CI/scripts.
</entering>

<updating_trap>
devenv update updates devenv.lock. Newer versions may introduce bugs — only update when necessary. If update breaks: restore previous lock from git or copy a working lock from another project.
</updating_trap>

<cleaning>
When devenv behaves strangely or builds fail unexpectedly: rm -rf .devenv/ .devenv.flake.nix removes cached state. Run devenv shell again to rebuild.
</cleaning>

<direnv>
DO NOT USE direnv. Unreliable, causes more issues than it solves. Always use devenv shell or devenv shell -- command directly.
</direnv>
