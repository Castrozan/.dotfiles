# Pull or merge request description

**Reader:** the reviewer today, and whoever finds this change in history next year wondering whether it is safe to
remove. The description must still match the change after review.

**Budget:** imperative title under 72 characters; a 1 to 3 sentence summary; 50 to 300 words in total, scaled by risk.
Fold logs and long evidence into `<details>`. Keep the change itself near 100 lines; past 1,000 it is too large to
review well.

**Shape:**

1. Title: one imperative sentence that stands alone ("Expire sessions on password change", not "Fix bug").
2. What changed and why, including the approach you rejected and the cost of the one you chose.
3. Linked issue, with enough context inline that the link is optional.
4. Before and after evidence for anything visible.
5. How to verify, as numbered steps.
6. The feedback you want.
7. User-facing change or release note, or "none".

**Visuals that earn their place:** a before | after table or screenshot pair; a GIF for an interaction; a diff for a
contract or config change; a benchmark table; a Mermaid sequence only when a cross-component flow changes.

**Avoid:** an unfilled template, "see ticket", a file-by-file narration of the diff, a screenshot of a terminal,
unmeasured claims like "faster".

## Example

Bad:

> **Fix bug**
> Fixed the issue with the cache.

Good:

```markdown
## Expire session cache entries on password change

Users stayed logged in on other devices for up to 24 h after changing their
password, because session entries only expired by TTL. This change deletes all
of a user's session entries when the password changes.

I chose delete-on-change over a shorter TTL, which would log everyone out more
often. Cost: one extra Redis SCAN per password change (p99 +4 ms in staging).

Closes #812.

### How to verify
1. Log in on two browsers as the same user.
2. Change the password in browser A.
3. Reload browser B: you land on the login page.

### Reviewer focus
Is a SCAN batch size of 500 sane for accounts with many sessions?

<details><summary>Staging latency, 1,000 password changes</summary>

| Metric | Before | After |
|---|---|---|
| p99 | 61 ms | 65 ms |

</details>
```

A visible change gets a side-by-side pair instead of a sentence:

```markdown
| Before | After |
|---|---|
| ![Settings page with the save button below the fold](before.png) | ![Settings page with a sticky save button](after.png) |
```

A contract change shows the exact edit:

```diff
- timeout_seconds: 30
+ timeout_seconds: 10
+ retries: 3
```

**Sources:** [Google CL descriptions](https://google.github.io/eng-practices/review/developer/cl-descriptions.html),
[Google small CLs](https://google.github.io/eng-practices/review/developer/small-cls.html),
[GitLab default MR template](https://gitlab.com/gitlab-org/gitlab/-/raw/master/.gitlab/merge_request_templates/Default.md).
