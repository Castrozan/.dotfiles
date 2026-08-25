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
    harness = f"""
global.fetch = async () => ({{ ok: true, json: () => {json.dumps([{"title": title} for title in titles])} }});
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
