import importlib.util
import json
from pathlib import Path
import shutil

import pytest


MODULE_PATH = Path(__file__).resolve().parents[2] / "source_inventory.py"
SPECIFICATION = importlib.util.spec_from_file_location("source_inventory", MODULE_PATH)
INVENTORY = importlib.util.module_from_spec(SPECIFICATION)
SPECIFICATION.loader.exec_module(INVENTORY)


@pytest.fixture
def bundle(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "resource.txt").write_text("owned resource")
    (source / "run").write_text("owned executable")
    (source / "run").chmod(0o755)
    emitted = tmp_path / "emitted"
    package = emitted / "plugin"
    shutil.copytree(source, package / "assets")
    for name in INVENTORY.GENERATED_FILES:
        path = package / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}")
    (package / "artifact-inventory.json").write_text(
        json.dumps({"artifacts": [{"name": "assets", "source": str(source)}]})
    )
    return emitted


def test_preservation_retains_source_counts_hashes_and_modes(bundle):
    result = INVENTORY.verify_preservation(bundle)
    assert (result["artifacts"], result["files"], result["metadataFiles"]) == (1, 2, 7)
    assert result["requiredFiles"][1]["executable"] is True


@pytest.mark.parametrize("mutation", ["corrupt", "missing", "mode", "extra"])
def test_damaged_delivery_is_not_rescued_by_valid_source(bundle, mutation):
    package = bundle / "plugin"
    if mutation == "corrupt":
        (package / "assets/resource.txt").write_text("corrupt")
    elif mutation == "missing":
        (package / "assets/resource.txt").unlink()
    elif mutation == "mode":
        (package / "assets/run").chmod(0o644)
    else:
        (package / "unexpected").write_text("foreign")
    with pytest.raises(ValueError):
        INVENTORY.verify_preservation(bundle)


@pytest.mark.parametrize("mutation", ["empty", "collision", "escape", "absent-source"])
def test_invalid_inventory_cannot_supply_preservation_evidence(bundle, mutation):
    path = bundle / "plugin/artifact-inventory.json"
    value = json.loads(path.read_text())
    if mutation == "empty":
        value["artifacts"] = []
    elif mutation == "collision":
        value["artifacts"] *= 2
    elif mutation == "escape":
        value["artifacts"][0]["name"] = "../escape"
    else:
        value["artifacts"][0]["source"] = str(bundle / "absent")
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError):
        INVENTORY.verify_preservation(bundle)


def test_single_file_sources_are_preserved(bundle):
    path = bundle / "plugin/artifact-inventory.json"
    original = json.loads(path.read_text())["artifacts"][0]
    path.write_text(
        json.dumps(
            {
                "artifacts": [
                    {
                        "name": f"assets/{name}",
                        "source": str(Path(original["source"]) / name),
                    }
                    for name in ("resource.txt", "run")
                ]
            }
        )
    )
    assert INVENTORY.verify_preservation(bundle)["artifacts"] == 2


def test_source_cycle_is_rejected_before_unbounded_traversal(bundle):
    source = bundle.parent / "source"
    (source / "cycle").symlink_to(source, target_is_directory=True)
    with pytest.raises(ValueError, match="cycle"):
        INVENTORY.verify_preservation(bundle)


def test_large_source_is_rejected_before_reading_bytes(bundle):
    source = bundle.parent / "source/resource.txt"
    with source.open("wb") as stream:
        stream.truncate(67108865)
    with pytest.raises(ValueError, match="resource limit"):
        INVENTORY.verify_preservation(bundle)


def test_emitted_link_cannot_escape_to_an_identical_source(bundle):
    delivered = bundle / "plugin/assets/resource.txt"
    delivered.unlink()
    delivered.symlink_to(bundle.parent / "source/resource.txt")
    with pytest.raises(ValueError, match="escapes"):
        INVENTORY.verify_preservation(bundle)
