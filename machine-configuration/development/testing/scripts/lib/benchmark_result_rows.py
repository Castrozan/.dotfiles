from collections.abc import Iterator
from dataclasses import dataclass


@dataclass(frozen=True)
class ValueAggregate:
    total: float
    count: int


def latest_value_by_key(
    data_lines: list[str],
    key_columns: tuple[int, ...],
    value_column: int,
) -> dict[str, float]:
    return dict(_keyed_values(data_lines, key_columns, value_column))


def aggregate_values_by_key(
    data_lines: list[str],
    key_columns: tuple[int, ...],
    value_column: int,
) -> dict[str, ValueAggregate]:
    aggregates: dict[str, ValueAggregate] = {}
    for key, value in _keyed_values(data_lines, key_columns, value_column):
        running = aggregates.get(key, ValueAggregate(0.0, 0))
        aggregates[key] = ValueAggregate(running.total + value, running.count + 1)
    return aggregates


def _keyed_values(
    data_lines: list[str],
    key_columns: tuple[int, ...],
    value_column: int,
) -> Iterator[tuple[str, float]]:
    required_field_count = max((*key_columns, value_column)) + 1
    for line in data_lines:
        fields = line.split(",")
        if len(fields) < required_field_count:
            continue
        try:
            value = float(fields[value_column])
        except ValueError:
            continue
        yield ",".join(fields[column] for column in key_columns), value


def recent_result_table_lines(result_lines: list[str], row_limit: int) -> list[str]:
    header = result_lines[0].split(",")
    recent = (
        result_lines[-row_limit:]
        if len(result_lines) > row_limit + 1
        else result_lines[1:]
    )
    rows = [line.split(",") for line in recent]
    column_widths = [len(column) for column in header]
    for fields in rows:
        for index, field in enumerate(fields):
            if index < len(column_widths):
                column_widths[index] = max(column_widths[index], len(field))
    row_format = "  ".join(f"{{:<{width}}}" for width in column_widths)
    return [row_format.format(*row) for row in (header, *rows)]
