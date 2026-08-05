from __future__ import annotations

import json
from pathlib import Path

TOKEN_USAGE_METRIC_NAME = "claude_code.token.usage"
COST_USAGE_METRIC_NAME = "claude_code.cost.usage"
TOKEN_TYPE_ATTRIBUTE_KEY = "type"
DELTA_AGGREGATION_TEMPORALITY = 1
CUMULATIVE_AGGREGATION_TEMPORALITY = 2


def default_otel_metrics_file_path() -> Path:
    return Path.home() / ".claude" / "otel-metrics" / "metrics.jsonl"


def read_otel_metrics_documents(metrics_file_path: Path) -> list[dict]:
    if not metrics_file_path.exists():
        return []
    documents = []
    for line in metrics_file_path.read_text().splitlines():
        stripped_line = line.strip()
        if not stripped_line:
            continue
        try:
            documents.append(json.loads(stripped_line))
        except json.JSONDecodeError:
            continue
    return documents


def _attribute_value_as_text(attribute_value: dict) -> str:
    for value_key in ("stringValue", "intValue", "doubleValue", "boolValue"):
        if value_key in attribute_value:
            return str(attribute_value[value_key])
    return ""


def _attributes_as_dict(data_point: dict) -> dict[str, str]:
    return {
        attribute["key"]: _attribute_value_as_text(attribute.get("value", {}))
        for attribute in data_point.get("attributes", [])
    }


def _data_point_numeric_value(data_point: dict) -> float:
    if "asInt" in data_point:
        return float(data_point["asInt"])
    if "asDouble" in data_point:
        return float(data_point["asDouble"])
    return 0.0


def _iter_metrics(documents: list[dict]):
    for document in documents:
        for resource_metrics in document.get("resourceMetrics", []):
            for scope_metrics in resource_metrics.get("scopeMetrics", []):
                for metric in scope_metrics.get("metrics", []):
                    yield metric


def _stream_key(attributes: dict[str, str]) -> tuple:
    return tuple(sorted(attributes.items()))


def _reduce_metric_streams(documents: list[dict], metric_name: str) -> list[dict]:
    cumulative_latest_value_by_stream: dict[tuple, dict] = {}
    delta_accumulated_value_by_stream: dict[tuple, dict] = {}
    for metric in _iter_metrics(documents):
        if metric.get("name") != metric_name:
            continue
        sum_metric = metric.get("sum", {})
        temporality = sum_metric.get(
            "aggregationTemporality", CUMULATIVE_AGGREGATION_TEMPORALITY
        )
        for data_point in sum_metric.get("dataPoints", []):
            attributes = _attributes_as_dict(data_point)
            stream_key = _stream_key(attributes)
            value = _data_point_numeric_value(data_point)
            if temporality == DELTA_AGGREGATION_TEMPORALITY:
                existing = delta_accumulated_value_by_stream.setdefault(
                    stream_key, {"attributes": attributes, "value": 0.0}
                )
                existing["value"] += value
            else:
                cumulative_latest_value_by_stream[stream_key] = {
                    "attributes": attributes,
                    "value": value,
                }
    return list(cumulative_latest_value_by_stream.values()) + list(
        delta_accumulated_value_by_stream.values()
    )


def summarize_token_usage_by_type(documents: list[dict]) -> dict[str, int]:
    token_usage_by_type: dict[str, int] = {}
    for stream in _reduce_metric_streams(documents, TOKEN_USAGE_METRIC_NAME):
        token_type = stream["attributes"].get(TOKEN_TYPE_ATTRIBUTE_KEY, "unknown")
        token_usage_by_type[token_type] = token_usage_by_type.get(token_type, 0) + int(
            stream["value"]
        )
    return token_usage_by_type


def summarize_total_cost_usd(documents: list[dict]) -> float:
    return round(
        sum(
            stream["value"]
            for stream in _reduce_metric_streams(documents, COST_USAGE_METRIC_NAME)
        ),
        4,
    )


def summarize_otel_metrics_documents(documents: list[dict]) -> dict:
    token_usage_by_type = summarize_token_usage_by_type(documents)
    total_cost_usd = summarize_total_cost_usd(documents)
    return {
        "token_usage_by_type": token_usage_by_type,
        "total_cost_usd": total_cost_usd,
        "has_data": bool(token_usage_by_type) or total_cost_usd > 0,
    }


def summarize_otel_metrics_file(metrics_file_path: Path) -> dict:
    return summarize_otel_metrics_documents(
        read_otel_metrics_documents(metrics_file_path)
    )
