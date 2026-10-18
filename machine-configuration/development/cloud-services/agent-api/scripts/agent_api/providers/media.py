import json
import shutil
from pathlib import Path

from agent_api.contract import MAXIMUM_ARTIFACT_BYTES, CapabilityError
from agent_api.files import file_digest, input_file, write_json
from agent_api.providers.processing import run_tool, tool


def media_command(request, directory, operation_id):
    if request.capability == "media.providers":
        return [tool("media-" + request.input["kind"]), "providers"]
    if request.capability == "movie.schema":
        return [tool("media-movie"), "schema"]
    kind, action = request.capability.split(".")
    command = [tool("media-" + kind), action]
    if kind in ("movie", "video"):
        data = {**request.input["request"], "operation_id": operation_id}
        path = directory / "media-request.json"
        write_json(path, data)
        return command + ["--request-file", str(path)]
    command.extend(["--operation-id", operation_id])
    for name, value in request.input.items():
        command.extend(["--" + name.replace("_", "-"), str(value)])
    return command


def media_artifact_source(artifact):
    if not isinstance(artifact, dict):
        return None
    if not isinstance(artifact.get("path"), str):
        return None
    path = Path(artifact["path"])
    return input_file(str(path)) if path.is_absolute() else None


def retain_media_artifact(source, target, artifact):
    shutil.copyfile(source, target)
    expected = artifact.get("sha256")
    if expected is not None and file_digest(target) != expected:
        raise CapabilityError("artifact_changed")
    artifact["gateway_path"] = str(target)


class MediaProvider:
    def preflight(self, request):
        pass

    def execute(self, request, directory, operation_id):
        command = media_command(request, directory, operation_id)
        discovery = request.capability in ("media.providers", "movie.schema")
        if not discovery:
            write_json(
                directory / "submission.json",
                {
                    "provider": "media",
                    "operation_id": operation_id,
                    "command": command[0],
                },
            )
        result = json.loads(run_tool(command, directory, request.timeout_seconds))
        if discovery:
            return result
        if result.get("status") != "succeeded":
            raise CapabilityError("media_operation_failed")
        self.retain_artifacts(result, directory)
        return result

    def retain_artifacts(self, receipt, directory):
        total_bytes = 0
        for name in ("image", "audio", "video", "thumbnail"):
            artifact = receipt.get("assets", {}).get(name, receipt.get(name))
            source = media_artifact_source(artifact)
            if source is None:
                continue
            total_bytes += source.stat().st_size
            if total_bytes > MAXIMUM_ARTIFACT_BYTES:
                raise CapabilityError("artifact_too_large")
            retain_media_artifact(source, directory / (name + source.suffix), artifact)
