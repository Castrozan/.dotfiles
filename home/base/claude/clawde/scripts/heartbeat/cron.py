import datetime


def cron_field_matches(field: str, value: int, minimum: int, maximum: int) -> bool:
    for part in field.split(","):
        range_specifier, _, step_text = part.partition("/")
        step = int(step_text) if step_text else 1
        if range_specifier == "*":
            start, end = minimum, maximum
        elif "-" in range_specifier:
            start_text, _, end_text = range_specifier.partition("-")
            start, end = int(start_text), int(end_text)
        else:
            start = int(range_specifier)
            end = maximum if step_text else start
        if start <= value <= end and (value - start) % step == 0:
            return True
    return False


def cron_expression_matches(expression: str, now: datetime.datetime) -> bool:
    minute, hour, day_of_month, month, day_of_week = expression.split()
    cron_day_of_week = now.isoweekday() % 7
    return (
        cron_field_matches(minute, now.minute, 0, 59)
        and cron_field_matches(hour, now.hour, 0, 23)
        and cron_field_matches(day_of_month, now.day, 1, 31)
        and cron_field_matches(month, now.month, 1, 12)
        and cron_field_matches(day_of_week, cron_day_of_week, 0, 6)
    )


def seconds_until_next_minute_boundary(now: datetime.datetime) -> float:
    return 60 - (now.second + now.microsecond / 1_000_000)
