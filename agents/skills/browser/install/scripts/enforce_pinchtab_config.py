import json
import os
import secrets
import sys
import tempfile

pinchtabConfigPath = os.path.expanduser("~/.pinchtab/config.json")

fullAccessSecurityAndHeadedDefaultPolicy = {
    "security": {
        "allowEvaluate": True,
        "allowMacro": True,
        "allowScreencast": True,
        "allowDownload": True,
        "allowCookies": True,
        "allowNetworkIntercept": True,
        "allowUpload": True,
        "allowClipboard": True,
        "allowStateExport": True,
        "enableActionGuards": False,
        "allowedDomains": ["*"],
        "downloadAllowedDomains": ["*"],
        "maxRedirects": -1,
        "attach": {
            "enabled": True,
            "allowHosts": ["*"],
            "allowSchemes": ["ws", "wss"],
        },
        "idpi": {
            "enabled": False,
            "strictMode": False,
            "scanContent": False,
            "wrapContent": False,
        },
    },
    "instanceDefaults": {
        "mode": "headed",
    },
}


def mergeEnforcedLeavesPreservingEverythingElse(currentConfig, enforcedPolicy):
    for key, enforcedValue in enforcedPolicy.items():
        currentValue = currentConfig.get(key)
        if isinstance(enforcedValue, dict) and isinstance(currentValue, dict):
            mergeEnforcedLeavesPreservingEverythingElse(currentValue, enforcedValue)
        else:
            currentConfig[key] = enforcedValue
    return currentConfig


def loadExistingConfigToleratingAbsenceButNeverClobberingCorruption(path):
    if not os.path.exists(path):
        return {}
    with open(path) as configHandle:
        return json.load(configHandle)


def ensureServerBearerTokenExistsSoAFreshMachineStartsAuthenticated(config):
    server = config.setdefault("server", {})
    if not server.get("token"):
        server["token"] = secrets.token_hex(24)


def atomicallyWriteConfigWithOwnerOnlyPermissions(path, config):
    directory = os.path.dirname(path)
    temporaryDescriptor, temporaryPath = tempfile.mkstemp(
        dir=directory, prefix=".config.", suffix=".json"
    )
    with os.fdopen(temporaryDescriptor, "w") as temporaryHandle:
        json.dump(config, temporaryHandle, indent=2)
    os.chmod(temporaryPath, 0o600)
    os.replace(temporaryPath, path)


def main():
    directory = os.path.dirname(pinchtabConfigPath)
    os.makedirs(directory, exist_ok=True)
    try:
        config = loadExistingConfigToleratingAbsenceButNeverClobberingCorruption(
            pinchtabConfigPath
        )
    except json.JSONDecodeError:
        print(
            f"enforce-pinchtab-config: {pinchtabConfigPath} is not valid JSON; leaving it untouched so the "
            "server-owned token and machine paths are never destroyed, and skipping enforcement this rebuild",
            file=sys.stderr,
        )
        return
    serializedBefore = json.dumps(config, sort_keys=True)
    mergeEnforcedLeavesPreservingEverythingElse(
        config, fullAccessSecurityAndHeadedDefaultPolicy
    )
    ensureServerBearerTokenExistsSoAFreshMachineStartsAuthenticated(config)
    if json.dumps(config, sort_keys=True) == serializedBefore:
        return
    atomicallyWriteConfigWithOwnerOnlyPermissions(pinchtabConfigPath, config)
    print(
        "enforce-pinchtab-config: reasserted full-capability, all-hosts, headed-default policy into "
        f"{pinchtabConfigPath} (a running server needs `pinchtab server restart` to pick it up)"
    )


if __name__ == "__main__":
    main()
