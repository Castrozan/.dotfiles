def selected_tests(
    config: dict,
    category: str | None,
    test_name: str | None,
    selected_test_keys: set[str] | None = None,
    partition: str | None = None,
) -> list:
    return [
        (test, category_name)
        for category_name, tests in config.get("tests", {}).items()
        if _matches_category(category, category_name)
        for test in tests
        if _is_selected(test, category_name, test_name, selected_test_keys, partition)
    ]


def _is_selected(
    test: dict,
    category_name: str,
    test_name: str | None,
    selected_test_keys: set[str] | None,
    partition: str | None,
) -> bool:
    key = f"{category_name}::{test['name']}"
    return _matches_test_selection(
        test, key, test_name, selected_test_keys
    ) and _matches_partition(test, partition)


def _matches_partition(test: dict, partition: str | None) -> bool:
    if partition is None:
        return True
    return test.get("held_out", False) == (partition == "held-out")


def _matches_category(category: str | None, category_name: str) -> bool:
    return not category or category_name == category


def _matches_test_selection(
    test: dict, key: str, test_name: str | None, selected_test_keys: set[str] | None
) -> bool:
    if test_name and test["name"] != test_name:
        return False
    if selected_test_keys is not None and key not in selected_test_keys:
        return False
    return True
