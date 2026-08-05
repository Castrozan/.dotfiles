import sys
from pathlib import Path

PROVISIONER_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_config_provisioner"
)
sys.path.insert(0, str(PROVISIONER_PACKAGE_DIRECTORY_PATH))

import quality_profile_provisioner  # noqa: E402


def stub_api(monkeypatch, custom_formats, profiles):
    updated = []
    resources = {"customformat": custom_formats, "qualityprofile": profiles}
    monkeypatch.setattr(
        quality_profile_provisioner,
        "get_resource_list",
        lambda base, key, resource: resources[resource],
    )
    monkeypatch.setattr(
        quality_profile_provisioner,
        "update_resource",
        lambda base, key, resource, resource_id, body: updated.append(
            (resource_id, body)
        ),
    )
    return updated


def stub_create(monkeypatch):
    created = []
    monkeypatch.setattr(
        quality_profile_provisioner,
        "create_resource",
        lambda base, key, resource, body: created.append((resource, body)),
    )
    return created
