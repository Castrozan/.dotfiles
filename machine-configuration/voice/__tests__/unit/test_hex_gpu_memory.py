from pathlib import Path

HEX_MODULE = Path(__file__).resolve().parents[2] / "hex-home-manager.nix"


def test_hex_transcribes_from_system_memory_when_the_graphics_card_is_full():
    assert '"GGML_VK_ALLOW_SYSMEM_FALLBACK=1"' in HEX_MODULE.read_text()
