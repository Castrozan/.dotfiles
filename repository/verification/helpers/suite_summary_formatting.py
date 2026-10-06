def format_tier_summary_line(tier_directory_name, tier_summary):
    if tier_summary is None:
        return None
    parts = []
    if tier_summary["bats_blocks"]:
        parts.append(f"{tier_summary['bats_blocks']} bats @test")
    if tier_summary["pytest_functions"]:
        parts.append(f"{tier_summary['pytest_functions']} pytest fn")
    return f"    {tier_directory_name}: {', '.join(parts)}"


def format_optional_summary_lines(summary):
    lines = []
    if summary["lua_test_file_count"]:
        lines.append(f"    lua: {summary['lua_test_file_count']} suite")
    if summary["has_qml_runner"]:
        lines.append("    qml: 1 suite")
    if summary["eval_yaml_count"]:
        lines.append(f"    evals: {summary['eval_yaml_count']} yaml")
    if summary["has_checks_nix"]:
        lines.append("    checks.nix: registered")
    return lines


def format_totals_footer(totals, nix_check_total):
    return (
        "\n=== Totals ===\n"
        f"  modules with tests: {totals['modules']}\n"
        f"  bats @test blocks:  {totals['bats_blocks']}\n"
        f"  pytest functions:   {totals['pytest_functions']}\n"
        f"  lua suites:         {totals['lua_suites']}\n"
        f"  qml suites:         {totals['qml_suites']}\n"
        f"  eval yamls:         {totals['eval_yamls']}\n"
        f"  nix checks:         {nix_check_total}"
    )
