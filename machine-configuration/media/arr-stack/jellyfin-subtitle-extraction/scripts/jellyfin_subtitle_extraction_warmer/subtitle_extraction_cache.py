import os

SUBTITLE_EXTRACTION_CACHE_DIRECTORY_NAME = "subtitles"
CODECS_EXTRACTED_UNDER_THEIR_OWN_EXTENSION = ("ass", "ssa")
FALLBACK_EXTRACTION_EXTENSION = "srt"
COMPACT_IDENTIFIER_LENGTH = 32


def dashed_media_source_identifier(media_source_identifier):
    compact_identifier = media_source_identifier.replace("-", "")
    if len(compact_identifier) != COMPACT_IDENTIFIER_LENGTH:
        return media_source_identifier
    return "-".join(
        [
            compact_identifier[:8],
            compact_identifier[8:12],
            compact_identifier[12:16],
            compact_identifier[16:20],
            compact_identifier[20:],
        ]
    )


def extraction_file_extension_for_codec(codec):
    normalized_codec = (codec or "").lower()
    if normalized_codec in CODECS_EXTRACTED_UNDER_THEIR_OWN_EXTENSION:
        return normalized_codec
    return FALLBACK_EXTRACTION_EXTENSION


def extraction_cache_path(
    jellyfin_data_directory, media_source_identifier, stream_index, codec
):
    dashed_identifier = dashed_media_source_identifier(media_source_identifier)
    return os.path.join(
        jellyfin_data_directory,
        SUBTITLE_EXTRACTION_CACHE_DIRECTORY_NAME,
        dashed_identifier[:2],
        dashed_identifier,
        f"{stream_index}.{extraction_file_extension_for_codec(codec)}",
    )


def embedded_text_subtitle_streams(media_source):
    return [
        stream
        for stream in media_source.get("MediaStreams") or []
        if stream.get("Type") == "Subtitle"
        and stream.get("IsTextSubtitleStream")
        and not stream.get("IsExternal")
    ]


def unextracted_subtitle_streams_of_item(
    item, jellyfin_data_directory, cache_path_exists=os.path.exists
):
    unextracted_streams = []
    for media_source in item.get("MediaSources") or []:
        media_source_identifier = media_source.get("Id") or item.get("Id")
        for stream in embedded_text_subtitle_streams(media_source):
            stream_index = stream.get("Index")
            codec = stream.get("Codec")
            if cache_path_exists(
                extraction_cache_path(
                    jellyfin_data_directory,
                    media_source_identifier,
                    stream_index,
                    codec,
                )
            ):
                continue
            unextracted_streams.append(
                {
                    "itemIdentifier": item.get("Id"),
                    "mediaSourceIdentifier": media_source_identifier,
                    "streamIndex": stream_index,
                    "requestedExtension": extraction_file_extension_for_codec(codec),
                }
            )
    return unextracted_streams


def subtitle_stream_request_path(unextracted_stream):
    return (
        f"/Videos/{unextracted_stream['itemIdentifier']}"
        f"/{unextracted_stream['mediaSourceIdentifier']}"
        f"/Subtitles/{unextracted_stream['streamIndex']}"
        f"/Stream.{unextracted_stream['requestedExtension']}"
    )


def someone_is_watching(sessions):
    return any(session.get("NowPlayingItem") for session in sessions)
