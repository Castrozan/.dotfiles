from run_evals_significance import (
    mcnemar_exact_p_value,
    paired_comparison,
    paired_hierarchical_bootstrap,
)


def test_no_discordant_pairs_is_not_significant():
    assert mcnemar_exact_p_value(0, 0) == 1.0


def test_all_discordant_in_one_direction_is_significant():
    assert mcnemar_exact_p_value(10, 0) < 0.05


def test_evenly_split_discordance_is_never_significant():
    assert mcnemar_exact_p_value(5, 5) == 1.0


def test_lopsided_small_sample_crosses_the_threshold():
    assert mcnemar_exact_p_value(8, 1) < 0.05


def test_paired_comparison_scores_rates_and_discordance():
    variant_a = {"t1": True, "t2": True, "t3": True, "t4": False}
    variant_b = {"t1": True, "t2": False, "t3": False, "t4": False}

    result = paired_comparison(variant_a, variant_b)

    assert result["n_paired"] == 4
    assert result["variant_a_pass_rate"] == 0.75
    assert result["variant_b_pass_rate"] == 0.25
    assert result["delta"] == 0.5
    assert result["a_only_wins"] == 2
    assert result["b_only_wins"] == 0
    assert result["both_pass"] == 1
    assert result["both_fail"] == 1


def test_paired_comparison_only_counts_shared_test_names():
    variant_a = {"shared": True, "a_only": True}
    variant_b = {"shared": False, "b_only": True}

    result = paired_comparison(variant_a, variant_b)

    assert result["n_paired"] == 1
    assert result["a_only_wins"] == 1


def test_repeated_comparison_resamples_cases_and_generations_deterministically():
    variant_a = {
        "reader_context": [True, True, True, True, True],
        "source_fidelity": [True, True, True, True, True],
    }
    variant_b = {
        "reader_context": [False, False, False, False, False],
        "source_fidelity": [True, True, True, True, True],
    }

    result = paired_hierarchical_bootstrap(
        variant_a, variant_b, iterations=2_000, seed=41
    )

    assert result["method"] == "paired_hierarchical_bootstrap"
    assert result["n_paired"] == 2
    assert result["sample_pairs"] == 10
    assert result["delta"] == 0.5
    assert result["lower_bound"] >= 0.0
    assert result["upper_bound"] > 0.0
    assert result["candidate_case_outcomes"] == variant_a
    assert result["control_case_outcomes"] == variant_b
    assert result == paired_hierarchical_bootstrap(
        variant_a, variant_b, iterations=2_000, seed=41
    )


def test_repeated_comparison_rejects_unpaired_generation_counts():
    try:
        paired_hierarchical_bootstrap({"case": [True]}, {"case": [True, False]})
    except ValueError as error:
        assert "same number of generations" in str(error)
    else:
        raise AssertionError("unpaired repeated samples must not be treated as pairs")


def test_repeated_comparison_names_cases_that_never_pass():
    result = paired_hierarchical_bootstrap(
        {"a": [False, False], "b": [True, False]},
        {"a": [True, True], "b": [False, False]},
        iterations=100,
    )
    assert result["candidate_hard_failures"] == ["a"]
    assert result["control_hard_failures"] == ["b"]
