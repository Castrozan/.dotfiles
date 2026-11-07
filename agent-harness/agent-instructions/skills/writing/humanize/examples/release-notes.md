# Release notes and changelog

**Reader:** a user deciding whether upgrading is safe and worth it.

**Budget:** at most 20 words per entry; 3 to 5 highlights per release.

**Shape:**

1. Version and ISO date, newest first.
2. Breaking changes first, prefixed **Breaking:**, with the migration step.
3. Entries grouped as Added, Changed, Deprecated, Removed, Fixed, Security.
4. Each entry starts with an imperative verb, stands alone, and links its pull request.

**Visuals that earn their place:** a screenshot per headline feature; a config diff for a migration; a deprecation
table (old | replacement | removal version).

**Avoid:** a git log dump, maintenance noise like formatting or dev dependencies, "various fixes".

## Example

```markdown
## [2.4.0] - 2026-11-07

### Changed
- **Breaking:** Require Node 20 or later; Node 18 is no longer tested. (#311)
- Retry failed uploads up to 3 times before reporting an error. (#298)

### Added
- Add `--dry-run` to `sync` to preview changes without writing. (#305)

### Fixed
- Fix crash when a config path contains spaces. (#309)
```

A migration shows the exact edit:

```diff
  sync:
-   target: s3://bucket
+   targets:
+     - s3://bucket
```

| Deprecated | Replacement | Removed in |
| --- | --- | --- |
| `--target` | `--targets` | 3.0 |

**Sources:** [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
[Common Changelog](https://common-changelog.org/), [Go 1.22 release notes](https://go.dev/doc/go1.22).
