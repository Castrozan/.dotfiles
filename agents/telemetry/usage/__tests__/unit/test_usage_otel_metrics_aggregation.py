import usage_otel_metrics_aggregation


class TestSumOtelMetrics:
    def test_empty_list_reports_no_data(self):
        summed = usage_otel_metrics_aggregation.sum_otel_metrics([])
        assert summed["has_data"] is False
        assert summed["token_usage_by_type"] == {}
        assert summed["total_cost_usd"] == 0

    def test_token_types_and_cost_are_summed_across_snapshots(self):
        summed = usage_otel_metrics_aggregation.sum_otel_metrics(
            [
                {
                    "token_usage_by_type": {"cacheRead": 1000, "output": 20},
                    "total_cost_usd": 1.2,
                    "has_data": True,
                },
                {
                    "token_usage_by_type": {"cacheRead": 500, "input": 7},
                    "total_cost_usd": 0.3,
                    "has_data": True,
                },
            ]
        )
        assert summed["token_usage_by_type"] == {
            "cacheRead": 1500,
            "output": 20,
            "input": 7,
        }
        assert summed["total_cost_usd"] == 1.5
        assert summed["has_data"] is True

    def test_missing_otel_keys_are_tolerated(self):
        summed = usage_otel_metrics_aggregation.sum_otel_metrics(
            [{}, {"has_data": False}]
        )
        assert summed["has_data"] is False
        assert summed["token_usage_by_type"] == {}
