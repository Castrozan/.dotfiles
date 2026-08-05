import argparse
import sys
import urllib.error

import jellyseerr_requests
import status_assembly
import status_formatting
import status_runtime_config


def build_argument_parser():
    parser = argparse.ArgumentParser(
        prog="arr-status",
        description="Show request and download status for media on the arr-stack",
    )
    parser.add_argument(
        "title",
        nargs="?",
        default=None,
        help="optional case-insensitive title substring to filter by",
    )
    return parser


def gather_status_lines():
    jellyseerr_base_url = status_runtime_config.jellyseerr_base_url()
    jellyseerr_api_key = status_runtime_config.read_jellyseerr_api_key()
    radarr_snapshot = status_assembly.snapshot_radarr(
        status_runtime_config.radarr_endpoint()
    )
    sonarr_snapshot = status_assembly.snapshot_sonarr(
        status_runtime_config.sonarr_endpoint()
    )

    status_lines = []
    for request_object in jellyseerr_requests.fetch_requests(
        jellyseerr_base_url, jellyseerr_api_key
    ):
        status_lines.append(
            status_assembly.build_status_line_tolerating_title_failure(
                jellyseerr_base_url,
                jellyseerr_api_key,
                request_object,
                radarr_snapshot,
                sonarr_snapshot,
            )
        )
    return status_lines


def main():
    arguments = build_argument_parser().parse_args()
    try:
        status_lines = gather_status_lines()
    except urllib.error.HTTPError as error:
        print(f"{error.code} from {error.url}", file=sys.stderr)
        raise SystemExit(1) from error
    except urllib.error.URLError as error:
        print(f"cannot reach Jellyseerr: {error.reason}", file=sys.stderr)
        raise SystemExit(1) from error

    filtered_status_lines = status_formatting.filter_by_title(
        status_lines, arguments.title
    )
    if not filtered_status_lines:
        print("no matching requests")
        return
    for status_line in filtered_status_lines:
        print(status_formatting.format_status_line(status_line))


if __name__ == "__main__":
    main()
