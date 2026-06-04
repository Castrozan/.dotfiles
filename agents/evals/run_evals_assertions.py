def check_assertions(output: str, assertions: dict) -> list[str]:
    failures = []

    if "output_contains" in assertions:
        for expected in assertions["output_contains"]:
            if expected.lower() not in output.lower():
                failures.append(f"Expected '{expected}' in output")

    if "output_not_contains" in assertions:
        for forbidden in assertions["output_not_contains"]:
            if forbidden.lower() in output.lower():
                failures.append(f"Unexpected '{forbidden}' in output")

    if "output_contains_any" in assertions:
        found = any(
            exp.lower() in output.lower() for exp in assertions["output_contains_any"]
        )
        if not found:
            failures.append(
                f"Expected one of {assertions['output_contains_any']} in output"
            )

    return failures
