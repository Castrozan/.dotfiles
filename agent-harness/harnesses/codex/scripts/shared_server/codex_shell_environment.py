from fnmatch import fnmatchcase


CORE_VARIABLES = {
    "PATH",
    "SHELL",
    "TMPDIR",
    "TEMP",
    "TMP",
    "HOME",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "LOGNAME",
    "USER",
}


def inherited_shell_environment(environment, policy):
    inheritance = policy.get("inherit", "all")
    excluded = list(policy.get("exclude", []))
    excluded.extend(
        pattern
        for pattern, action in policy.get("filters", {}).items()
        if action == "exclude"
    )
    if not policy.get("ignore_default_excludes", True):
        excluded.extend(["*KEY*", "*SECRET*", "*TOKEN*"])
    return {
        name: value
        for name, value in environment.items()
        if inheritance != "none"
        and (inheritance != "core" or name.upper() in CORE_VARIABLES)
        and not any(fnmatchcase(name.upper(), pattern.upper()) for pattern in excluded)
        and name not in {"CODEX_THREAD_ID", "DOTFILES_CODEX_SHARED_SERVER"}
        and not name.startswith("CODEX_INTERNAL_")
    }


def client_shell_policy(environment, policy):
    policy = {name: value for name, value in policy.items() if value is not None}
    return {
        **policy,
        "inherit": "none",
        "set": {
            **inherited_shell_environment(environment, policy),
            **policy.get("set", {}),
        },
    }
