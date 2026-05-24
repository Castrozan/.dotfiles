from pathlib import Path

import memory_recall


class TestSelectTopRecallPaths:
    def test_orders_by_score_descending(self):
        scores = {Path("low.md"): 1, Path("high.md"): 5, Path("mid.md"): 3}
        result = memory_recall.select_top_recall_paths(scores)
        assert result == [Path("high.md"), Path("mid.md"), Path("low.md")]

    def test_caps_at_max_recall_paths(self):
        scores = {Path(f"f{index}.md"): index for index in range(20)}
        result = memory_recall.select_top_recall_paths(scores)
        assert len(result) <= memory_recall.MAX_RECALL_PATHS
