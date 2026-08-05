from __future__ import annotations


def sum_otel_metrics(otel_metrics_list: list[dict]) -> dict:
    token_usage_by_type: dict[str, int] = {}
    total_cost_usd = 0.0
    for otel_metrics in otel_metrics_list:
        for token_type, token_count in otel_metrics.get(
            "token_usage_by_type", {}
        ).items():
            token_usage_by_type[token_type] = (
                token_usage_by_type.get(token_type, 0) + token_count
            )
        total_cost_usd += otel_metrics.get("total_cost_usd", 0)
    return {
        "token_usage_by_type": token_usage_by_type,
        "total_cost_usd": round(total_cost_usd, 4),
        "has_data": bool(token_usage_by_type) or total_cost_usd > 0,
    }
