from pathlib import Path

VOICE = Path(__file__).resolve().parents[2]


def test_every_system_selects_the_multilingual_model_the_wake_prefers():
    linux = (VOICE / "hex-home-manager.nix").read_text()
    mac = (VOICE / "hex-darwin-home-manager.nix").read_text()
    assert 'model = "parakeet_v3";' in linux
    assert "model use parakeet_v3 || run ${hexCommand} model install parakeet_v3" in mac
