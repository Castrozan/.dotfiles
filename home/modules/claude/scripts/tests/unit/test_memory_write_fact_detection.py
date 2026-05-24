import memory_write


class TestFactAlreadyPresent:
    def test_detects_exact_match(self):
        existing = "# user\n\n- 2026-05-17: lucas prefers pnpm over npm\n"
        assert memory_write.fact_already_present(
            existing, "lucas prefers pnpm over npm"
        )

    def test_detects_match_case_insensitive(self):
        existing = "# user\n\n- LUCAS PREFERS PNPM\n"
        assert memory_write.fact_already_present(existing, "lucas prefers pnpm")

    def test_detects_match_with_surrounding_whitespace(self):
        existing = "# user\n\n- 2026-05-17: lucas prefers pnpm\n"
        assert memory_write.fact_already_present(existing, "  lucas prefers pnpm  ")

    def test_returns_false_when_fact_missing(self):
        existing = "# user\n\n- 2026-05-17: lucas prefers vim\n"
        assert not memory_write.fact_already_present(existing, "lucas prefers emacs")
