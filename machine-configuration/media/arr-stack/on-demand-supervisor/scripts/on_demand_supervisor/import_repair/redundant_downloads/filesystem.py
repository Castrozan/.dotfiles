from pathlib import PurePosixPath
from urllib.parse import urlencode

from import_repair.redundant_downloads.eligibility import (
    positive_identifier,
    scoped_path,
)

MAX_LIBRARY_DIRECTORIES = 4


def directory_contents(read, directory):
    return read(
        "filesystem?"
        + urlencode({"path": str(directory) + "/", "includeFiles": "true"})
    )


def directory_files(contents):
    return {PurePosixPath(item["path"]): item for item in contents.get("files", [])}


def file_matches(file, size):
    return file.get("type") == "file" and file.get("size") == size


def matching_files(actual_files, expected_files):
    return all(
        file_matches(actual_files.get(path, {}), size)
        for path, size in expected_files.items()
    )


def directory_inventory_matches(contents, files, expected_files):
    return not contents.get("directories") and set(files) == set(expected_files)


def source_files_verified(record, download, read):
    output_path = PurePosixPath(record["outputPath"])
    single_file = set(download.source_files) == {output_path}
    directory = output_path.parent if single_file else output_path
    contents = directory_contents(read, directory)
    files = directory_files(contents)
    if not single_file and not directory_inventory_matches(
        contents, files, download.source_files
    ):
        return False
    return matching_files(files, download.source_files)


def current_episode_matches(episode, series_id, file_id):
    return (
        episode.get("seriesId") == series_id
        and episode.get("hasFile") is True
        and episode.get("episodeFileId") == file_id
    )


def library_file_path(file, series_id):
    if file.get("seriesId") != series_id or not positive_identifier(file.get("size")):
        return None
    return scoped_path(file.get("path"), "/data/media")


def records_by_identifier(records):
    return {record["id"]: record for record in records}


def library_episode_files(record, download, read):
    query = urlencode({"seriesId": record["seriesId"]})
    episodes = records_by_identifier(read("episode?" + query))
    files = records_by_identifier(read("episodefile?" + query))
    library_files = {}
    for episode_id, file_id in download.episode_files.items():
        if not current_episode_matches(
            episodes.get(episode_id, {}), record["seriesId"], file_id
        ):
            return None
        file = files.get(file_id, {})
        path = library_file_path(file, record["seriesId"])
        if path is None:
            return None
        library_files[path] = file["size"]
    return library_files


def library_files_verified(record, download, read):
    files = library_episode_files(record, download, read)
    if not files:
        return False
    directories = {path.parent for path in files}
    if len(directories) > MAX_LIBRARY_DIRECTORIES:
        return False
    actual_files = {}
    for directory in sorted(directories):
        actual_files.update(directory_files(directory_contents(read, directory)))
    return matching_files(actual_files, files)
