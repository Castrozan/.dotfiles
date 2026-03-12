---
name: pull
description: Pull request and merge request management. Use when user asks to view PR/MR comments, review feedback, iterate on changes, manage remote branches, or work with GitHub/GitLab pull requests.
---

<announcement>
"I'm using the pull skill to manage PR/MR feedback and iteration."
</announcement>

<understanding_feedback>
Categorize comments: blocking (request changes), suggestions (nice-to-have), questions (need response), nits (style/minor). Prioritize blocking comments. Identify patterns across multiple comments. Note which reviewer made each comment for context.
</understanding_feedback>

<iteration_workflow>
Fetch all comments and reviews, group by file and severity. Address blocking comments first. For each change: edit, verify, commit with reference to feedback. Respond to questions in PR if needed. Push changes and request re-review.
</iteration_workflow>

<commit_messages>
Reference the feedback in commit messages. For single items: fix(component): address review - use const instead of let. For multiple: fix: address PR feedback - consistent naming, error handling, dead code removal.
</commit_messages>

<platform_detection>
For GitLab repositories (remote URL contains "gitlab"), use glab CLI instead of gh. Both tools have comprehensive --help for all operations.
</platform_detection>

<red_flags>
Never dismiss reviews without addressing concerns. Always verify CI passes before requesting re-review. Don't mark conversations resolved without actually fixing the issue.
</red_flags>
