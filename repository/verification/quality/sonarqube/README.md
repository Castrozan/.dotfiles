# SonarQube without an IDE

The public repository uses the free [OSS plan](https://docs.sonarsource.com/sonarqube-cloud/administering-sonarcloud/managing-subscription/subscription-plans#oss-plan)
in `castrozan-oss`. This plan permits custom quality gates and profiles. The separate Free plan does not.

## Configuration authority

[sonar-project.properties](../../../../sonar-project.properties) defines analysis scope, test classification, reports, and
scanner settings. [cloud.json](cloud.json) defines the project's quality gate, inherited language profiles, rule
parameters, and Cloud settings. Nix supplies the official `sonar` CLI, `sonar-scanner`, and the API-only Sonar MCP server.

Rebuild after changing the JSON so the installed command receives the new policy, then apply it from the repository root:

```sh
rebuild
sonar-configure
```

The apply command uses the official CLI's authenticated API transport. Repeated applies converge on the declared
conditions and custom rule overrides. It preserves the upstream Sonar way profiles and changes only this project's
named profiles and gate. Removing an override from the JSON removes it from the custom profile. Pushes to `main` apply
the policy before analysis; pull requests use the deployed policy.

The GitHub app installation and account credential are bootstrap requirements. Sonar requires app reinstallation to
[move a GitHub organization binding](https://docs.sonarsource.com/sonarqube-cloud/administering-sonarcloud/creating-organization/changing-organization-binding).
Normal scans, rule changes, and issue retrieval require no browser.

## Agent access

```sh
sonar list issues --project Castrozan_.dotfiles
sonar quality-gate status --project Castrozan_.dotfiles --format json
sonar api get '/api/rules/show?key=python:S104&organization=castrozan-oss'
sonar-scanner
```

The [official CLI](https://github.com/SonarSource/sonarqube-cli) returns JSON for issue listings and API calls; quality-gate
status requires `--format json`. Claude Code, Codex, and OpenCode
also receive a read-only MCP server for issues, rules, gates, duplication, coverage, and metrics. The CLI provides the
same access from other harnesses. No IDE analysis toolset is enabled.

The local credential comes from agenix at `~/.secrets/sonarqube-token`. GitHub Actions uses a separate `SONAR_TOKEN`
secret. Rotate both before the expiration recorded in the account's access-token settings. Sonar also revokes tokens
after 60 days of inactivity. Credentials are never stored in scanner properties or the Nix store. Explicit
`SONARQUBE_CLI_TOKEN`, `SONARQUBE_CLI_SERVER`, and `SONARQUBE_CLI_ORG` values support another account or server.

## Coverage and enforcement

CI imports Python coverage from both pytest tiers and fails when the Sonar gate fails. The configured coverage scope
is Python; JavaScript/TypeScript and shell coverage are excluded until their runners produce compatible reports.
Fork pull requests run the ordinary tests but skip the credentialed Cloud scan. A failing CI job does not itself
prohibit merging unless GitHub branch protection requires that check.

The shared post-edit hook and CI enforce at most 15 immediate files and folders combined in Git repositories.
The counter includes tracked files and untracked files not ignored by Git, including Markdown and hidden files.
It excludes Git metadata, ignored generated files, and submodule contents; each submodule or symlink counts as one
entry. Empty untracked directories do not count because Git does not version them. The hook checks the edited
path's ancestors; CI checks the whole repository and catches shell-created entries too.

Existing oversized directories have explicit ceilings in
[directory baseline](../directory-entries/baseline.json), matching the existing file-length adoption model.
They may shrink but cannot grow; CI requires lowering or removing a ceiling after a directory shrinks.
The default limit remains 15. The existing 200-physical-line counter applies to code extensions, not Markdown,
and retains its separate recorded ceilings. Post-edit hook failures report the violation after the edit; they do
not undo a write.

Sonar computes the first quality gate after the second analysis of a new project. The initial analysis establishes
the baseline. Scans retain their complete configured scope, including when only a few files changed.

## Capability gaps

| Requirement                                      | Sonar coverage                                       | Complement or limitation                                                                                                            |
| ------------------------------------------------ | ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Semantic code, security, duplication, complexity | Language-specific analyzers and configurable rules   | Language coverage is broad, not universal.                                                                                          |
| Nix                                              | No native analyzer                                   | Existing nixfmt, statix, deadnix, and Nix checks remain authoritative.                                                              |
| QML and Lua                                      | No native analyzers                                  | Existing QML lint and Lua tests remain in CI.                                                                                       |
| Markdown                                         | Secret detection is explicitly enabled               | No Markdown style, prose, link, or instruction-quality analyzer; existing instruction checks remain separate.                       |
| 200 physical lines per code file                 | S104 set to 200 for Python and JavaScript/TypeScript | Existing shared hook/CI counter covers other code extensions and legacy ceilings. Sonar's rule is not the cross-language authority. |
| 15 immediate files and folders per directory     | No native structural rule                            | Shared hook and CI count immediate entries, with recorded ceilings for existing violations. This is excessive directory fan-out.    |
| Custom semantic or cross-file rules              | Configure existing rules and supported templates     | Cloud cannot load arbitrary analyzer plugins; run custom analyzers separately and import external issues.                           |
| Partial feedback                                 | PR analysis and analyzer caches                      | Full scanner scope must remain intact; narrowing it to changed files can erase project findings.                                    |
| Immediate local diff analysis                    | Separate Agentic Analysis/Vortex capability          | Requires the relevant paid entitlement; this setup uses CI scanning and API retrieval.                                              |
| Every coding convention                          | Incomplete                                           | Language linters, formatters, architecture checks, and behavioral tests remain necessary.                                           |

Sonar accepts [external analyzer reports](https://docs.sonarsource.com/sonarqube-cloud/analyzing-source-code/importing-external-issues/external-analyzer-reports),
but importing findings does not execute their checks or make their rule definitions editable in a Sonar profile.
Keep each companion check's own exit status in CI. See the official
[incremental analysis](https://docs.sonarsource.com/sonarqube-cloud/analyzing-source-code/incremental-analysis-mechanisms)
and [Agent Essentials](https://docs.sonarsource.com/sonarqube-cloud/administering-sonarcloud/managing-subscription/signing-up-for-plan#agent-essentials)
documentation for the limits of faster feedback.
