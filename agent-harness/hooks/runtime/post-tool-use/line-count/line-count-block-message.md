# A file went over the line limit

Split it into modules that each do one thing. Two rules govern where the
pieces land.

Do not leave the new siblings loose in a generic catch-all folder. When the
split puts two or more related files into `scripts/`, `lib/`, `utils/`, or a
flat hooks directory, give them a subfolder named for their domain.

Reference such a folder from nix by the directory, not by the single entry
file, so the sibling modules resolve from the same store path.
