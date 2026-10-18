import os
from pathlib import Path

from agent_api.contract import CapabilityError


def credential_available(description):
    environment = description.get("credential_environment")
    filename = description.get("credential_file")
    if environment is None:
        return None
    return (
        bool(os.environ.get(environment))
        or (Path.home() / ".secrets" / filename).is_file()
    )


def read_credential(environment, filename, required=True):
    credential = os.environ.get(environment)
    if not credential:
        try:
            credential = (Path.home() / ".secrets" / filename).read_text().strip()
        except FileNotFoundError:
            credential = None
    if required and not credential:
        raise CapabilityError("missing_credentials")
    return credential
