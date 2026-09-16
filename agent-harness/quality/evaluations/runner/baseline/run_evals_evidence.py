def raise_for_evaluation_errors(results: list, context: str = "evaluation") -> None:
    errors = [
        f"{result.category}/{result.name}: {result.error}"
        for result in results
        if result.error
    ]
    if errors:
        raise RuntimeError(f"{context} has invocation errors: " + "; ".join(errors))
