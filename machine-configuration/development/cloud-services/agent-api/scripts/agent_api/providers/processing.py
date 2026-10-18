import json
import os
import subprocess

from agent_api.contract import MAXIMUM_RESULT_BYTES, CapabilityError
from agent_api.files import input_file


def tool(name):
    return os.environ.get("AGENT_API_" + name.upper().replace("-", "_"), name)


def run_tool(arguments, directory, timeout_seconds):
    output = directory / "command-output.json"
    with output.open("wb") as stream, (directory / "command.log").open("ab") as log:
        try:
            process = subprocess.run(
                arguments,
                stdin=subprocess.DEVNULL,
                stdout=stream,
                stderr=log,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            raise CapabilityError("deadline_exceeded") from None
    if process.returncode:
        raise CapabilityError("tool_failed")
    if output.stat().st_size > MAXIMUM_RESULT_BYTES:
        raise CapabilityError("response_too_large")
    return output.read_bytes()


class ProcessingProvider:
    def preflight(self, request):
        input_file(request.input["path"])
        if "model_path" in request.input:
            model = input_file(request.input["model_path"])
            language = request.input.get("language", "auto")
            if ".en." in model.name and language != "en":
                raise CapabilityError("english_model_requires_english")

    def execute(self, request, directory, operation_id):
        path = str(input_file(request.input["path"]))
        if request.capability == "media.probe":
            data = run_tool(
                [
                    tool("ffprobe"),
                    "-v",
                    "error",
                    "-show_format",
                    "-show_streams",
                    "-of",
                    "json",
                    path,
                ],
                directory,
                request.timeout_seconds,
            )
            return json.loads(data)
        if request.capability == "document.convert":
            data = run_tool(
                [
                    tool("pandoc"),
                    "--sandbox",
                    "--from=" + request.input["format"],
                    "--to=gfm",
                    path,
                ],
                directory,
                request.timeout_seconds,
            )
            (directory / "document.md").write_bytes(data)
            return {"artifact": "document.md", "markdown": data.decode("utf-8")}
        audio_path = directory / "audio.wav"
        run_tool(
            [
                tool("ffmpeg"),
                "-nostdin",
                "-v",
                "error",
                "-i",
                path,
                "-map",
                "0:a:0",
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-c:a",
                "pcm_s16le",
                "-threads",
                "2",
                str(audio_path),
            ],
            directory,
            request.timeout_seconds,
        )
        if request.capability == "audio.extract":
            return {"artifact": audio_path.name, "sample_rate": 16000, "channels": 1}
        model_path = str(input_file(request.input["model_path"]))
        prefix = directory / "transcript"
        run_tool(
            [
                tool("whisper-cli"),
                "--model",
                model_path,
                "--file",
                str(audio_path),
                "--threads",
                "2",
                "--language",
                request.input.get("language", "auto"),
                "--output-json",
                "--output-txt",
                "--output-srt",
                "--output-file",
                str(prefix),
                "--no-prints",
            ],
            directory,
            request.timeout_seconds,
        )
        transcript = prefix.with_suffix(".json")
        if transcript.stat().st_size > MAXIMUM_RESULT_BYTES:
            raise CapabilityError("response_too_large")
        return {
            "transcript": json.loads(transcript.read_bytes()),
            "text": prefix.with_suffix(".txt").read_text(),
            "subtitles": "transcript.srt",
            "model": model_path,
        }
