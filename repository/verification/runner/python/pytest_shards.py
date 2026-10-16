import json
import math
from pathlib import Path
import sys


def _validate_shard_inputs(test_files, shard_index, shard_count):
    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise ValueError(
            "shard index must be nonnegative and smaller than a positive shard count"
        )
    if len(set(test_files)) != len(test_files):
        raise ValueError("shard discovery contains duplicate test files")


def _validate_weights(weights):
    if any(not math.isfinite(weight) or weight <= 0 for weight in weights.values()):
        raise ValueError("shard weights must be finite positive durations")


def _weight_test_files(test_files, repository_directory, weights):
    repository_directory = Path(repository_directory).resolve()
    default_weight = max(1.0, max(weights.values(), default=1.0))
    return [
        (
            path,
            weights.get(
                Path(path).resolve().relative_to(repository_directory).as_posix(),
                default_weight,
            ),
        )
        for path in test_files
    ]


def select_shard(test_files, repository_directory, shard_index, shard_count, weights):
    _validate_shard_inputs(test_files, shard_index, shard_count)
    _validate_weights(weights)
    weighted_files = _weight_test_files(test_files, repository_directory, weights)
    partitions = [[] for _ in range(shard_count)]
    durations = [0.0] * shard_count
    for path, weight in sorted(weighted_files, key=lambda item: (-item[1], item[0])):
        destination = min(
            range(shard_count), key=lambda index: (durations[index], index)
        )
        partitions[destination].append(path)
        durations[destination] += weight
    return sorted(partitions[shard_index])


def main(arguments):
    try:
        repository_directory, shard_index, shard_count, *test_files = arguments
        weights = json.loads(
            Path(__file__).with_name("pytest_integration_weights.json").read_text()
        )
        selected_files = select_shard(
            test_files,
            repository_directory,
            int(shard_index),
            int(shard_count),
            weights,
        )
    except (OSError, TypeError, ValueError) as error:
        print(f"ERROR: pytest shard selection failed: {error}", file=sys.stderr)
        return 1
    for path in selected_files:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
