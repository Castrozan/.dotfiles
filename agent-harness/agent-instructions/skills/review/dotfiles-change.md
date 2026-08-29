<core-authority>
Core `<evidence>`, `<completion>`, and `<coding>` own persistent judgment, verification, and code-quality defaults;
`SKILL.md` owns the review method, finding contract, severity, and verdict. This file owns only the bounded dotfiles
pre-push review procedure.
</core-authority>

<mandate>
A substantive dotfiles review runs inside the current harness after the change is committed and before it is pushed. It
launches no workflow and no reviewer subagent, and stays read-only until its verdict is delivered. Repository context
decides when a change is substantive.
</mandate>

<procedure>
Review exactly the commits the task added: 1) recover the intended outcome, the constraints, and
the behavior that must not change before reading any diff; 2) identify the exact task commit range and the absolute
repository root, anchoring every later command at that root against sibling checkouts; 3) read one whole-range diff plus
its stat, excluding shared working-tree state and unrelated commits; 4) inspect changed lines, callers, tests, and
deployment edges through all six lenses (logic, Nix, style, instructions, coverage, exposure); 5) trace each changed
path through realistic inputs, failure states, ordering, resource use, security boundaries, and downstream consumers;
6) prove or discard every candidate with file-and-line evidence before reporting it; 7) compare delivery to every user
requirement and to the behavior that must stay unchanged; 8) report findings under the parent skill contract or
`No findings.`, naming the range, files, and lenses reviewed and closing with a verdict on whether the goal is achieved.
</procedure>

<follow-up>
Fix confirmed findings in cohesive follow-up commits and repeat the procedure; never amend the reviewed commit, because
peers may already have built on it.
</follow-up>
