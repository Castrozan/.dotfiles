### Machine local wrapper repo

Beyond the shared dotfiles checkout, @hostname@ also owns a private machine-local wrapper repo at
@localWrapperRepoPath@: a standalone git repo with its own origin, not a submodule and not part of the fleet, no CI and
no peer stewards, whose flake is what this machine actually builds by importing the public dotfiles and layering a
private overlay on top.

Keep it reconciled with its own origin/main under the same invariant you hold for the dotfiles repo: pull `--ff-only`
when it is behind, and when it holds validated local commits ahead and the machine builds green, push it
fast-forward-only; never `git push --force`, never reset or rewrite history to force agreement, stage specific files
only, and escalate to the operator on any non-fast-forward divergence you cannot cleanly resolve.

Its green proof is the ordinary rebuild you already run for this machine, since that rebuild reads this wrapper. Treat
it purely as a second repo you keep synced, never a peer to coordinate with, and never let its private contents cross
into the shared dotfiles repo.

### Chise validation launcher

Launch every chise validation through
`scripts/validation/start_detached_validation_of_head.py` in the steward workspace. It owns the systemd scope, pinned
wrapper build, log, and revision-keyed result sentinel. Never replace it with a raw background `nix build`: a successful
build can finish silently, leaving no verdict and making the next tick misclassify success as missing evidence.
