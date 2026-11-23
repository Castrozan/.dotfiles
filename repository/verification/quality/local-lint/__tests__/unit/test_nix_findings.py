import nix_findings


def test_statix_keeps_rule_and_precise_location():
    reports = [
        {
            "file": "source.nix",
            "report": [
                {
                    "code": 4,
                    "diagnostics": [
                        {
                            "at": {"from": {"line": 3, "column": 8}},
                            "message": "Use inherit",
                        }
                    ],
                }
            ],
        }
    ]
    finding = list(nix_findings.statix_diagnostics(reports))[0]
    assert finding["code"]["value"] == "statix-4"
    assert finding["location"]["range"]["start"] == {"line": 3, "column": 8}


def test_deadnix_keeps_separate_binding_findings():
    reports = [
        {
            "file": "source.nix",
            "results": [
                {"line": 1, "column": 2, "message": "Unused lambda pattern"},
                {"line": 7, "column": 4, "message": "Unused let binding"},
            ],
        }
    ]
    assert len(list(nix_findings.deadnix_diagnostics(reports))) == 2
