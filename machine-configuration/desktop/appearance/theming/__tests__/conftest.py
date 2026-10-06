import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

COLOR_GENERATION_DIRECTORY = Path(__file__).resolve().parent.parent / "color-generation"
sys.path.insert(0, str(COLOR_GENERATION_DIRECTORY))

colorthief_module_stub = ModuleType("colorthief")
colorthief_module_stub.ColorThief = MagicMock

pil_module_stub = ModuleType("PIL")
pil_image_module_stub = ModuleType("PIL.Image")
pil_module_stub.Image = pil_image_module_stub
with patch.dict(
    sys.modules,
    {
        "colorthief": colorthief_module_stub,
        "PIL": pil_module_stub,
        "PIL.Image": pil_image_module_stub,
    },
):
    import regenerate_wallpaper_derived_colors as orchestrator
    import theme_generate_from_wallpaper as theme_generator

sys.modules[orchestrator.__name__] = orchestrator
sys.modules[theme_generator.__name__] = theme_generator


@pytest.fixture
def create_theme_directory():
    def create(
        themes_directory,
        theme_name,
        *,
        is_wallpaper_derived,
        background_filenames,
        existing_colors_toml=None,
    ):
        theme_directory = themes_directory / theme_name
        backgrounds_directory = theme_directory / "backgrounds"
        backgrounds_directory.mkdir(parents=True)
        for background_filename in background_filenames:
            (backgrounds_directory / background_filename).write_bytes(b"image-bytes")
        if is_wallpaper_derived:
            (theme_directory / "wallpaper-derived.mode").write_text("")
        if existing_colors_toml is not None:
            (theme_directory / "colors.toml").write_text(existing_colors_toml)
        return theme_directory

    return create


@pytest.fixture
def record_staged_paths(monkeypatch):
    staged_paths = []
    monkeypatch.setattr(
        orchestrator,
        "stage_path_in_repository",
        lambda dotfiles_directory, path_to_stage: staged_paths.append(path_to_stage),
    )
    return staged_paths
