import json

import claude_otel_metrics_reader


def _token_usage_document(token_type, value, temporality, metric_name=None):
    return {
        "resourceMetrics": [
            {
                "resource": {},
                "scopeMetrics": [
                    {
                        "scope": {},
                        "metrics": [
                            {
                                "name": metric_name
                                or claude_otel_metrics_reader.TOKEN_USAGE_METRIC_NAME,
                                "sum": {
                                    "aggregationTemporality": temporality,
                                    "dataPoints": [
                                        {
                                            "attributes": [
                                                {
                                                    "key": "type",
                                                    "value": {
                                                        "stringValue": token_type
                                                    },
                                                }
                                            ],
                                            "asInt": str(value),
                                        }
                                    ],
                                },
                            }
                        ],
                    }
                ],
            }
        ]
    }


def _cost_document(value, model=None):
    attributes = [{"key": "model", "value": {"stringValue": model}}] if model else []
    return {
        "resourceMetrics": [
            {
                "resource": {},
                "scopeMetrics": [
                    {
                        "scope": {},
                        "metrics": [
                            {
                                "name": claude_otel_metrics_reader.COST_USAGE_METRIC_NAME,
                                "sum": {
                                    "aggregationTemporality": claude_otel_metrics_reader.CUMULATIVE_AGGREGATION_TEMPORALITY,
                                    "dataPoints": [
                                        {"attributes": attributes, "asDouble": value}
                                    ],
                                },
                            }
                        ],
                    }
                ],
            }
        ]
    }


class TestReadOtelMetricsDocuments:
    def test_missing_file_returns_empty(self, tmp_path):
        assert (
            claude_otel_metrics_reader.read_otel_metrics_documents(
                tmp_path / "absent.jsonl"
            )
            == []
        )

    def test_blank_and_corrupt_lines_are_skipped(self, tmp_path):
        metrics_file_path = tmp_path / "metrics.jsonl"
        metrics_file_path.write_text(
            "\n".join(
                [
                    json.dumps(_cost_document("1.5")),
                    "",
                    "{ not json",
                    json.dumps(_cost_document("2.5")),
                ]
            )
        )
        documents = claude_otel_metrics_reader.read_otel_metrics_documents(
            metrics_file_path
        )
        assert len(documents) == 2


class TestSummarizeTokenUsageByType:
    def test_cumulative_keeps_latest_value_per_stream(self):
        cumulative = claude_otel_metrics_reader.CUMULATIVE_AGGREGATION_TEMPORALITY
        documents = [
            _token_usage_document("cacheRead", 1000, cumulative),
            _token_usage_document("cacheRead", 4200, cumulative),
            _token_usage_document("output", 50, cumulative),
        ]
        assert claude_otel_metrics_reader.summarize_token_usage_by_type(documents) == {
            "cacheRead": 4200,
            "output": 50,
        }

    def test_delta_accumulates_value_per_stream(self):
        delta = claude_otel_metrics_reader.DELTA_AGGREGATION_TEMPORALITY
        documents = [
            _token_usage_document("output", 10, delta),
            _token_usage_document("output", 15, delta),
        ]
        assert claude_otel_metrics_reader.summarize_token_usage_by_type(documents) == {
            "output": 25
        }


class TestSummarizeOtelMetricsDocuments:
    def test_cumulative_cost_keeps_latest_per_stream(self):
        documents = [_cost_document("0.5"), _cost_document("1.234567")]
        assert claude_otel_metrics_reader.summarize_total_cost_usd(documents) == 1.2346

    def test_distinct_cost_streams_are_summed_and_rounded(self):
        documents = [
            _cost_document("1.234567", model="opus"),
            _cost_document("0.1", model="haiku"),
        ]
        assert claude_otel_metrics_reader.summarize_total_cost_usd(documents) == 1.3346

    def test_summary_reports_has_data_false_when_empty(self):
        summary = claude_otel_metrics_reader.summarize_otel_metrics_documents([])
        assert summary["has_data"] is False
        assert summary["token_usage_by_type"] == {}
        assert summary["total_cost_usd"] == 0

    def test_summary_folds_tokens_and_cost(self):
        cumulative = claude_otel_metrics_reader.CUMULATIVE_AGGREGATION_TEMPORALITY
        summary = claude_otel_metrics_reader.summarize_otel_metrics_documents(
            [
                _token_usage_document("cacheRead", 9000, cumulative),
                _cost_document("3.5"),
            ]
        )
        assert summary["has_data"] is True
        assert summary["token_usage_by_type"] == {"cacheRead": 9000}
        assert summary["total_cost_usd"] == 3.5

    def test_summarize_file_reads_then_summarizes(self, tmp_path):
        cumulative = claude_otel_metrics_reader.CUMULATIVE_AGGREGATION_TEMPORALITY
        metrics_file_path = tmp_path / "metrics.jsonl"
        metrics_file_path.write_text(
            json.dumps(_token_usage_document("input", 42, cumulative))
        )
        summary = claude_otel_metrics_reader.summarize_otel_metrics_file(
            metrics_file_path
        )
        assert summary["token_usage_by_type"] == {"input": 42}
