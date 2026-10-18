def object_schema(properties, required):
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def text(maximum=4096):
    return {"type": "string", "minLength": 1, "maxLength": maximum}


def capability(identifier, provider, description, input_schema, payment="none"):
    return {
        "id": identifier,
        "provider": provider,
        "description": description,
        "payment": payment,
        "input_schema": input_schema,
    }


def local_capabilities():
    return [
        capability(
            "web.extract",
            "trafilatura",
            "Fetch a page and extract its main text and links without a browser.",
            object_schema({"url": text()}, ["url"]),
        ),
        capability(
            "web.download",
            "http",
            "Download one HTTP resource into a retained private artifact, up to 512 MiB.",
            object_schema({"url": text()}, ["url"]),
        ),
        capability(
            "download.metadata",
            "yt-dlp",
            "Inspect one supported media URL without downloading its media.",
            object_schema({"url": text()}, ["url"]),
        ),
        capability(
            "download.media",
            "yt-dlp",
            "Download one video or audio URL; playlists and automatic retries are disabled.",
            object_schema({"url": text(), "audio_only": {"type": "boolean"}}, ["url"]),
        ),
        capability(
            "media.probe",
            "ffmpeg",
            "Inspect local audio or video streams and duration.",
            object_schema({"path": text()}, ["path"]),
        ),
        capability(
            "audio.extract",
            "ffmpeg",
            "Convert local media into mono 16 kHz PCM WAV for transcription.",
            object_schema({"path": text()}, ["path"]),
        ),
        capability(
            "audio.transcribe",
            "whisper-cpp",
            "Transcribe local audio/video into JSON, text and SRT using supplied local weights.",
            object_schema(
                {"path": text(), "model_path": text(), "language": text(20)},
                ["path", "model_path"],
            ),
        ),
        capability(
            "document.convert",
            "pandoc",
            "Convert a local document to GitHub Markdown using Pandoc's sandbox.",
            object_schema(
                {
                    "path": text(),
                    "format": {
                        "enum": [
                            "docx",
                            "epub",
                            "html",
                            "markdown",
                            "rst",
                            "org",
                            "latex",
                        ]
                    },
                },
                ["path", "format"],
            ),
        ),
    ]
