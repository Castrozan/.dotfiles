import stat
import sys

from remove_distrusted_certificates_from_bundle import main, remove_distrusted_segments

BUNDLE_HEADER = "# $OpenBSD: cert.pem,v 1.22.2.1 2021/09/30 18:28:20 deraadt Exp $\n"


def certificate_entry(distinguished_name: str) -> str:
    return (
        f"=== {distinguished_name}\n"
        "Certificate:\n"
        f"        Subject: {distinguished_name}\n"
        "-----BEGIN CERTIFICATE-----\n"
        "MIIB\n"
        "-----END CERTIFICATE-----\n"
    )


TRUSTED_ENTRY = certificate_entry(
    "/C=US/O=Internet Security Research Group/CN=ISRG Root X1"
)
EMSIGN_ENTRY = certificate_entry(
    "/C=IN/OU=emSign PKI/O=eMudhra Technologies Limited/CN=emSign ECC Root CA - G3"
)
EMSIGN_SIBLING_ENTRY = certificate_entry(
    "/C=IN/OU=emSign PKI/O=eMudhra Technologies Limited/CN=emSign Root CA - G1"
)
AAA_ENTRY = certificate_entry(
    "/C=GB/ST=Greater Manchester/L=Salford/O=Comodo CA Limited/CN=AAA Certificate Services"
)

BUNDLE = (
    BUNDLE_HEADER
    + "### Comodo CA Limited\n\n"
    + AAA_ENTRY
    + "\n### eMudhra Technologies Limited\n\n"
    + EMSIGN_ENTRY
    + "\n"
    + EMSIGN_SIBLING_ENTRY
    + "\n### Internet Security Research Group\n\n"
    + TRUSTED_ENTRY
)

DISTRUSTED_COMMON_NAMES = {"emSign ECC Root CA - G3", "AAA Certificate Services"}


def run_main(monkeypatch, bundle_path):
    argv = [
        "remove-distrusted-certificates-from-bundle",
        "--bundle-path",
        str(bundle_path),
    ]
    for common_name in sorted(DISTRUSTED_COMMON_NAMES):
        argv += ["--distrusted-common-name", common_name]
    monkeypatch.setattr(sys, "argv", argv)
    return main()


def test_removes_only_entries_issued_to_distrusted_common_names():
    filtered_text, removed = remove_distrusted_segments(BUNDLE, DISTRUSTED_COMMON_NAMES)

    assert "CN=emSign ECC Root CA - G3" not in filtered_text
    assert "CN=AAA Certificate Services" not in filtered_text
    assert EMSIGN_SIBLING_ENTRY in filtered_text
    assert TRUSTED_ENTRY in filtered_text
    assert filtered_text.count("-----BEGIN CERTIFICATE-----") == 2
    assert sorted(removed) == sorted(
        [
            "/C=IN/OU=emSign PKI/O=eMudhra Technologies Limited/CN=emSign ECC Root CA - G3",
            "/C=GB/ST=Greater Manchester/L=Salford/O=Comodo CA Limited/CN=AAA Certificate Services",
        ]
    )


def test_keeps_header_and_organization_headings():
    filtered_text, _ = remove_distrusted_segments(BUNDLE, DISTRUSTED_COMMON_NAMES)

    assert filtered_text.startswith(BUNDLE_HEADER)
    assert "### Internet Security Research Group\n" in filtered_text


def test_common_name_must_match_whole_trailing_component():
    filtered_text, removed = remove_distrusted_segments(BUNDLE, {"Root CA - G3"})

    assert removed == []
    assert filtered_text == BUNDLE


def test_rewrites_bundle_in_place_preserving_mode(tmp_path, monkeypatch):
    bundle_path = tmp_path / "cert.pem"
    bundle_path.write_text(BUNDLE)
    bundle_path.chmod(0o644)

    assert run_main(monkeypatch, bundle_path) == 0

    assert "emSign ECC Root CA - G3" not in bundle_path.read_text()
    assert stat.S_IMODE(bundle_path.stat().st_mode) == 0o644
    assert list(tmp_path.iterdir()) == [bundle_path]


def test_second_run_leaves_already_filtered_bundle_untouched(tmp_path, monkeypatch):
    bundle_path = tmp_path / "cert.pem"
    bundle_path.write_text(BUNDLE)
    run_main(monkeypatch, bundle_path)
    filtered_modification_time = bundle_path.stat().st_mtime_ns
    filtered_text = bundle_path.read_text()

    assert run_main(monkeypatch, bundle_path) == 0

    assert bundle_path.read_text() == filtered_text
    assert bundle_path.stat().st_mtime_ns == filtered_modification_time


def test_absent_bundle_is_not_an_error(tmp_path, monkeypatch):
    assert run_main(monkeypatch, tmp_path / "missing.pem") == 0
