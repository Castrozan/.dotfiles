from run_evals_significance import mcnemar_exact_p_value, paired_comparison


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
