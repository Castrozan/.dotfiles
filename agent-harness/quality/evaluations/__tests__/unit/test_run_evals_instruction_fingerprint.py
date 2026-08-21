from run_evals_fingerprint import digest_instruction_paths, instruction_wording


def write_instruction(directory, text):
    path = directory / "surface.md"
    path.write_text(text, encoding="utf-8")
    return digest_instruction_paths(directory, {path})


def test_capitalizing_a_label_leaves_the_evidence_authorized(tmp_path):
    lowercase = write_instruction(tmp_path, "**brief:** the standing purpose.")
    capitalized = write_instruction(tmp_path, "**Brief:** the standing purpose.")

    assert lowercase == capitalized


def test_rewrapping_a_paragraph_leaves_the_evidence_authorized(tmp_path):
    one_line = write_instruction(tmp_path, "Keep unrelated work out of the reply.")
    rewrapped = write_instruction(tmp_path, "Keep unrelated work\nout of the reply.")

    assert one_line == rewrapped


def test_changing_a_rule_invalidates_the_evidence(tmp_path):
    before = write_instruction(tmp_path, "Keep unrelated work out of the reply.")
    after = write_instruction(tmp_path, "Put unrelated work in the reply.")

    assert before != after


def test_wording_drops_emphasis_case_and_wrapping_only(tmp_path):
    assert instruction_wording("**Brief:**\nthe  gate") == "brief: the gate"
