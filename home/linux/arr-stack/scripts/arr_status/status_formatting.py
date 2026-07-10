def format_status_line(status_line):
    title_with_year = status_line.title
    if status_line.year:
        title_with_year = f"{status_line.title} ({status_line.year})"
    return (
        f"{title_with_year}\t{status_line.media_type}"
        f"\t{status_line.requested_by}\t{stage_text(status_line)}"
    )


def stage_text(status_line):
    if status_line.progress is not None:
        text = f"{status_line.stage} | downloading {status_line.progress['percent']}%"
        if status_line.progress["time_left"]:
            text += f" ETA {status_line.progress['time_left']}"
        return text
    if status_line.stage == "processing" and not status_line.arr_reachable:
        return "processing (download chain idle)"
    return status_line.stage


def filter_by_title(status_lines, title_query):
    if not title_query:
        return status_lines
    lowered_query = title_query.lower()
    return [
        status_line
        for status_line in status_lines
        if lowered_query in (status_line.title or "").lower()
    ]
