import sys
from pathlib import Path

PROVISIONER_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_config_provisioner"
)
sys.path.insert(0, str(PROVISIONER_PACKAGE_DIRECTORY_PATH))

import provisioner_core


def test_provision_all_continues_after_a_failing_step(monkeypatch):
    attempted = []

    def failing_first_step(configuration, step, dry_run):
        attempted.append(step["resource"])
        if len(attempted) == 1:
            raise RuntimeError("first step failed")

    monkeypatch.setattr(provisioner_core, "provision_step", failing_first_step)
    monkeypatch.setattr(
        provisioner_core,
        "provision_quality_profile_step",
        lambda configuration, step, dry_run: None,
    )
    failed_steps = provisioner_core.provision_all({}, False)
    assert len(attempted) == len(provisioner_core.RESOURCE_PLAN)
    assert failed_steps == 1


def test_provision_all_reports_zero_failures_on_clean_run(monkeypatch):
    monkeypatch.setattr(
        provisioner_core, "provision_step", lambda configuration, step, dry_run: None
    )
    monkeypatch.setattr(
        provisioner_core,
        "provision_quality_profile_step",
        lambda configuration, step, dry_run: None,
    )
    assert provisioner_core.provision_all({}, False) == 0


def test_provision_all_counts_failing_quality_profile_steps(monkeypatch):
    monkeypatch.setattr(
        provisioner_core, "provision_step", lambda configuration, step, dry_run: None
    )

    def failing_quality_profile_step(configuration, step, dry_run):
        raise RuntimeError("quality profile step failed")

    monkeypatch.setattr(
        provisioner_core,
        "provision_quality_profile_step",
        failing_quality_profile_step,
    )
    failed_steps = provisioner_core.provision_all({}, False)
    assert failed_steps == len(provisioner_core.QUALITY_PROFILE_PLAN)
