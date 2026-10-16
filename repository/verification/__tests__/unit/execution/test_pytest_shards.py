import importlib.util
from pathlib import Path

import pytest

RUNNER_DIRECTORY = Path(__file__).resolve().parents[3] / "runner"


@pytest.fixture
def selector():
    specification = importlib.util.spec_from_file_location(
        "pytest_shards", RUNNER_DIRECTORY / "pytest_shards.py"
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module.select_shard


def test_weighted_partition_balances_files_and_preserves_exact_union(
    selector, tmp_path
):
    weights = {"test_a.py": 8, "test_b.py": 7, "test_c.py": 6, "test_d.py": 5}
    paths = [str(tmp_path / name) for name in weights]
    shards = [selector(paths, tmp_path, index, 2, weights) for index in range(2)]
    assert set(shards[0]).isdisjoint(shards[1])
    assert sorted(shards[0] + shards[1]) == sorted(paths)
    assert [sum(weights[Path(path).name] for path in shard) for shard in shards] == [
        13,
        13,
    ]
    assert shards == [
        selector(list(reversed(paths)), tmp_path, index, 2, weights)
        for index in range(2)
    ]


def test_new_files_are_retained_and_empty_shards_are_valid(selector, tmp_path):
    paths = [str(tmp_path / name) for name in ("test_known.py", "test_new.py")]
    shards = [
        selector(paths, tmp_path, index, 4, {"test_known.py": 12}) for index in range(4)
    ]
    assert sorted(path for shard in shards for path in shard) == sorted(paths)
    assert sorted(len(shard) for shard in shards) == [0, 0, 1, 1]
    assert selector([], tmp_path, 0, 2, {}) == []


@pytest.mark.parametrize("index,count", [(-1, 2), (2, 2), (0, 0), (0, -1)])
def test_invalid_shard_ranges_are_rejected(selector, tmp_path, index, count):
    with pytest.raises(ValueError):
        selector([], tmp_path, index, count, {})


def test_duplicate_files_and_files_outside_repository_are_rejected(selector, tmp_path):
    path = str(tmp_path / "test_a.py")
    with pytest.raises(ValueError):
        selector([path, path], tmp_path, 0, 1, {})
    with pytest.raises(ValueError):
        selector([str(tmp_path.parent / "test_a.py")], tmp_path, 0, 1, {})
