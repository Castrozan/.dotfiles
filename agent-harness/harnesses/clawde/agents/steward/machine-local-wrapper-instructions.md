### Machine local wrapper repo

Beyond the shared dotfiles checkout, @hostname@ also owns a private machine-local wrapper repo at
@localWrapperRepoPath@: a standalone git repo with its own origin, not a submodule and not part of the fleet, no CI and
no peer stewards, whose flake is what this machine actually builds by importing the public dotfiles and layering a
private overlay on top.

Treat it purely as a second repo kept fast-forward-synced with its own origin, never a peer to coordinate with, and
never let its private contents cross into the shared dotfiles repo.
