from jsonschema import Draft202012Validator

from agent_api.catalogs.cloud import cloud_capabilities
from agent_api.catalogs.local import local_capabilities
from agent_api.catalogs.media import media_capabilities
from agent_api.contract import CapabilityError
from agent_api.providers.credentials import credential_available

PROVIDERS = {
    "trafilatura": {
        "execution": "local",
        "documentation": "https://trafilatura.readthedocs.io/",
    },
    "http": {"execution": "local", "documentation": "https://www.python-httpx.org/"},
    "yt-dlp": {
        "execution": "local",
        "documentation": "https://github.com/yt-dlp/yt-dlp",
    },
    "ffmpeg": {
        "execution": "local",
        "documentation": "https://ffmpeg.org/documentation.html",
    },
    "whisper-cpp": {
        "execution": "local",
        "documentation": "https://github.com/ggml-org/whisper.cpp",
    },
    "pandoc": {"execution": "local", "documentation": "https://pandoc.org/MANUAL.html"},
    "media": {
        "execution": "local_and_cloud",
        "documentation": "media-image providers; media-speech providers; media-movie schema",
    },
    "monid": {
        "execution": "cloud",
        "credential_environment": "MONID_API_KEY",
        "credential_file": "monid-api-key",
        "documentation": "https://docs.monid.ai/",
    },
    "fal": {
        "execution": "cloud",
        "credential_environment": "FAL_KEY",
        "credential_file": "fal-api-key",
        "documentation": "https://fal.ai/docs/documentation/model-apis/inference/queue",
    },
    "firecrawl": {
        "execution": "cloud",
        "credential_environment": "FIRECRAWL_API_KEY",
        "credential_file": "firecrawl-api-key",
        "documentation": "https://docs.firecrawl.dev/",
        "unauthenticated_access": "limited",
    },
}


def providers():
    return [
        {
            "id": name,
            **description,
            "credentials_available": credential_available(description),
        }
        for name, description in PROVIDERS.items()
    ]


def capabilities(query="", provider=None):
    entries = local_capabilities() + media_capabilities() + cloud_capabilities()
    words = query.lower().split()
    return [
        entry
        for entry in entries
        if (provider is None or provider == entry["provider"])
        and all(
            word in (entry["id"] + " " + entry["description"]).lower() for word in words
        )
    ]


def describe(capability_id):
    entry = next(
        (entry for entry in capabilities() if entry["id"] == capability_id), None
    )
    if entry is None:
        raise CapabilityError("unsupported_capability")
    return entry


def discover(query="", provider=None):
    return [
        {key: value for key, value in entry.items() if key != "input_schema"}
        for entry in capabilities(query, provider)
    ]


def validate_input(request):
    entry = describe(request.capability)
    if next(
        Draft202012Validator(entry["input_schema"]).iter_errors(request.input), None
    ):
        raise CapabilityError("invalid_input")
    return entry


def validate_request(request):
    entry = validate_input(request)
    payment = entry["payment"]
    requires_payment = payment == "provider_plan"
    if payment == "speech_provider":
        requires_payment = request.input["provider"] != "kokoro"
    if payment == "optional_account":
        requires_payment = credential_available(PROVIDERS[entry["provider"]])
    if requires_payment and not request.allow_paid:
        raise CapabilityError("payment_permission_required")
    return entry
