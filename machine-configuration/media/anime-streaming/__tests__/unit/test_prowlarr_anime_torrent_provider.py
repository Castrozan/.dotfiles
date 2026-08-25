import json
import subprocess
from pathlib import Path


PROVIDER_PATH = (
    Path(__file__).resolve().parents[2] / "prowlarr-anime-torrent-provider.js"
)


def provider_episode_numbers(titles):
    harness = f"""
const provider = new globalThis.Provider();
const titles = {json.dumps(titles)};
console.log(JSON.stringify(titles.map((title) => provider.toAnimeTorrent({{ title }}).episodeNumber)));
"""
    result = subprocess.run(
        ["node", "-"],
        input=PROVIDER_PATH.read_text(encoding="utf-8") + harness,
        capture_output=True,
        check=True,
        text=True,
    )
    return json.loads(result.stdout)


def smart_search_episode_numbers(titles, episode_number):
    results = [
        {"title": title, "categories": [{"id": 5070, "name": "TV/Anime"}]}
        for title in titles
    ]
    harness = f"""
global.fetch = async () => ({{ ok: true, json: () => {json.dumps(results)} }});
const provider = new globalThis.Provider();
provider.prowlarrBaseUrl = "http://127.0.0.1:9696";
provider.prowlarrApiKey = "runtime-secret";
provider.smartSearch({{ query: "LIAR GAME", episodeNumber: {episode_number}, resolution: "1080p", batch: false }}).then((results) => {{
  console.log(JSON.stringify(results.map((result) => result.episodeNumber)));
}});
"""
    result = subprocess.run(
        ["node", "-"],
        input=PROVIDER_PATH.read_text(encoding="utf-8") + harness,
        capture_output=True,
        check=True,
        text=True,
    )
    return json.loads(result.stdout)


def smart_search_category_selection(results):
    harness = f"""
let requestedUrl = "";
global.fetch = async (url) => {{
  requestedUrl = url;
  return {{ ok: true, json: () => {json.dumps(results)} }};
}};
const provider = new globalThis.Provider();
provider.prowlarrBaseUrl = "http://127.0.0.1:9696";
provider.prowlarrApiKey = "runtime-secret";
provider.smartSearch({{ query: "LIAR GAME", episodeNumber: 1, resolution: "1080p", batch: false }}).then((matches) => {{
  console.log(JSON.stringify({{ requestedUrl, titles: matches.map((match) => match.name) }}));
}});
"""
    result = subprocess.run(
        ["node", "-"],
        input=PROVIDER_PATH.read_text(encoding="utf-8") + harness,
        capture_output=True,
        check=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_extracts_episode_numbers_without_confusing_years_or_resolutions():
    assert provider_episode_numbers(
        [
            "[ASW] LIAR GAME  21 [1080p HEVC x265 10Bit][AAC]",
            "LIAR GAME (2026) S01E21 SUBFRENCH 1080p WEB-DL",
            "[SubsPlease] LIAR GAME - 01 [1080p].mkv",
            "[Group] LIAR GAME Episode 7 [720p]",
            "LIAR GAME (2026) Complete 1080p",
        ]
    ) == [21, 21, 1, 7, -1]


def test_smart_search_discards_results_for_other_episodes():
    assert smart_search_episode_numbers(
        [
            "[ASW] LIAR GAME  21 [1080p HEVC x265 10Bit][AAC]",
            "[SubsPlease] LIAR GAME - 01 [1080p].mkv",
            "LIAR GAME (2026) Complete 1080p",
        ],
        1,
    ) == [1]


def test_smart_search_requests_and_keeps_only_anime_results():
    selection = smart_search_category_selection(
        [
            {
                "title": "LIAR GAME 2026 S01E01 live action 1080p",
                "categories": [{"id": 5040, "name": "TV/HD"}],
            },
            {
                "title": "[SubsPlease] LIAR GAME - 01 [1080p].mkv",
                "categories": [{"id": 5070, "name": "TV/Anime"}],
            },
        ]
    )

    assert "categories=5070" in selection["requestedUrl"]
    assert selection["titles"] == ["[SubsPlease] LIAR GAME - 01 [1080p].mkv"]
