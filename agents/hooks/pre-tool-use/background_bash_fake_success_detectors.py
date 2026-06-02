import re


def command_uses_until_loop_terminating_on_empty_count(command_string):
    return bool(
        re.search(
            r"until\b[\s\S]*?\[\s*\"?\$\([\s\S]+?\)\"?\s*=\s*\"?0\"?\s*\][\s\S]*?\bsleep\b",
            command_string,
        )
    )


def command_filters_by_hardcoded_long_literal_used_in_count_or_test(command_string):
    has_jq_select_with_long_literal = bool(
        re.search(
            r"select\s*\(\s*\.[A-Za-z_][\w.]*\s*==\s*\"[A-Za-z0-9_./-]{8,}\"\s*\)",
            command_string,
        )
    )
    has_downstream_count_or_zero_test = bool(
        re.search(r"\blength\b|\bwc\s+-l\b|=\s*\"?0\"?", command_string)
    )
    return has_jq_select_with_long_literal and has_downstream_count_or_zero_test


def command_pipes_count_into_test_against_literal_zero(command_string):
    return bool(
        re.search(
            r"\[\s*\"?\$\([^)]*\b(?:length|wc\s+-l)\b[^)]*\)\"?\s*=\s*\"?0\"?\s*\]",
            command_string,
        )
    )
