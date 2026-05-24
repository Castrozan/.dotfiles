#!/usr/bin/env bash

_run_skill_frontmatter_validation() {
	echo "--- Skill Frontmatter Validation ---"
	"$REPO_DIR/agents/evals/validate-skill-frontmatter.sh" "$REPO_DIR/agents/skills"
	echo ""
}
