def command_first_token_basename(command_text: str) -> str:
    command_tokens = command_text.split()
    if not command_tokens:
        return ""
    return command_tokens[0].split("/")[-1]


def sum_process_cpu_percent(ps_output: str, command_predicate) -> float:
    total_cpu_percent = 0.0
    for line in ps_output.splitlines():
        line_parts = line.strip().split(None, 1)
        if len(line_parts) != 2:
            continue
        if command_predicate(line_parts[1]):
            try:
                total_cpu_percent += float(line_parts[0])
            except ValueError:
                continue
    return round(total_cpu_percent, 1)


def sum_process_rss_kilobytes_by_pattern(
    ps_output: str, command_patterns: dict, include_total: bool
) -> dict:
    rss_kilobytes_by_key = {key: 0 for key in command_patterns}
    total_rss_kilobytes = 0
    for line in ps_output.splitlines():
        line_parts = line.strip().split(None, 1)
        if len(line_parts) != 2:
            continue
        try:
            process_rss_kilobytes = int(line_parts[0])
        except ValueError:
            continue
        command_text = line_parts[1]
        total_rss_kilobytes += process_rss_kilobytes
        for key, command_pattern in command_patterns.items():
            if command_pattern in command_text:
                rss_kilobytes_by_key[key] += process_rss_kilobytes
    if include_total:
        rss_kilobytes_by_key["total"] = total_rss_kilobytes
    return rss_kilobytes_by_key
