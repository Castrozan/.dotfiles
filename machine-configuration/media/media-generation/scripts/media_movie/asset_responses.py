import json

from media_movie.contract import MovieError


def read_asset_response(path):
    if path.stat().st_size > 1024 * 1024:
        raise MovieError("invalid_asset_receipt")
    try:
        result = json.loads(path.read_bytes())
    except (ValueError, OSError):
        raise MovieError("invalid_asset_receipt") from None
    if not isinstance(result, dict):
        raise MovieError("invalid_asset_receipt")
    return result


def reported_error(line):
    try:
        reported = json.loads(line)
    except ValueError:
        return None
    if not isinstance(reported, dict) or not isinstance(reported.get("error"), str):
        return None
    return reported["error"]


def asset_error_category(path, default_category):
    if not path.exists() or path.stat().st_size > 1024 * 1024:
        return default_category
    for line in reversed(path.read_text(encoding="utf-8").splitlines()):
        category = reported_error(line)
        if category is not None:
            return category
    return default_category
