from steward_test_helpers import repository_status

ALL_CLEAR = {
    "superproject_divergence": False,
    "needs_sync": False,
    "submodule_divergence": False,
    "needs_submodule_sync": False,
    "needs_validation": False,
    "needs_submodule_push": False,
    "needs_push": False,
    "continuous_integration_failing": False,
    "has_mail": False,
    "continuous_integration_pending": False,
}


def verdict_for(**overrides):
    return repository_status.classify_verdict(**{**ALL_CLEAR, **overrides})


def test_clean_when_nothing_pending():
    assert verdict_for() == "clean"


def test_nonff_divergence_outranks_sync_and_everything():
    assert (
        verdict_for(
            superproject_divergence=True,
            needs_sync=True,
            submodule_divergence=True,
            needs_validation=True,
            needs_push=True,
        )
        == "superproject_divergence"
    )


def test_pure_behind_is_needs_sync():
    assert verdict_for(needs_sync=True) == "needs_sync"


def test_pure_ahead_is_needs_push():
    assert verdict_for(needs_push=True) == "needs_push"


def test_validation_precedes_submodule_push():
    assert (
        verdict_for(needs_validation=True, needs_submodule_push=True)
        == "needs_validation"
    )


def test_submodule_divergence_precedes_validation():
    assert (
        verdict_for(submodule_divergence=True, needs_validation=True)
        == "submodule_divergence"
    )
