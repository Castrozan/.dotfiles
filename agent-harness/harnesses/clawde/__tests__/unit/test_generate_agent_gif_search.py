import generate_agent_gif_search
import pytest
from agent_media_workspace import MediaRequestRefused

TIERS = ("hd", "md", "sm", "xs")
LIFELIKE_SIZES = (21_000_000, 6_000_000, 780_000, 230_000)


def gif_item(title="Cursed Cat", sizes=LIFELIKE_SIZES):
    return {
        "title": title,
        "file": {
            tier: {
                "gif": {
                    "url": f"https://cdn.klipy.test/{title}/{tier}.gif",
                    "size": size,
                }
            }
            for tier, size in zip(TIERS, sizes)
        },
    }


def stub_klipy(monkeypatch, items):
    seen = {"searched": None, "downloaded": []}

    def answer(url):
        seen["searched"] = url
        return {"result": True, "data": {"data": items}}

    def download(url):
        seen["downloaded"].append(url)
        return b"GIF89a"

    monkeypatch.setattr(generate_agent_gif_search, "get_json", answer)
    monkeypatch.setattr(generate_agent_gif_search, "fetch_bytes", download)
    return seen


@pytest.fixture
def searching_agent(media_agent_workspace, monkeypatch):
    monkeypatch.chdir(media_agent_workspace)
    return media_agent_workspace


def test_takes_the_largest_tier_that_still_fits():
    chosen = generate_agent_gif_search.choose_rendition(gif_item(), 7_000_000)
    assert chosen.endswith("/md.gif")


def test_refuses_a_candidate_whose_every_tier_is_oversized():
    oversized = gif_item(sizes=(30_000_000,) * 4)
    assert generate_agent_gif_search.choose_rendition(oversized, 1_000_000) is None


def test_a_query_searches_and_an_empty_query_trends():
    searched = generate_agent_gif_search.build_url("key", "cursed cat", 3, "monster")
    trending = generate_agent_gif_search.build_url("key", "", 3, "monster")
    assert "/gifs/search?q=cursed%20cat" in searched
    assert "customer_id=monster" in searched and "per_page=3" in searched
    assert "/gifs/trending" in trending


def test_brings_back_a_small_file_to_judge_and_a_good_one_to_send(
    searching_agent, monkeypatch, capsys
):
    stub_klipy(monkeypatch, [gif_item()])

    assert generate_agent_gif_search.main(["--query", "cursed cat"]) == 0

    reported = capsys.readouterr().out
    assert "candidate 1: Cursed Cat" in reported
    written = sorted(path.name for path in (searching_agent / "media").glob("*.gif"))
    assert len(written) == 2
    assert any(name.startswith("gif-look-") for name in written)


def test_one_file_is_enough_when_the_same_tier_serves_both(
    searching_agent, monkeypatch, capsys
):
    stub_klipy(monkeypatch, [gif_item(sizes=(400_000,) * 4)])

    assert generate_agent_gif_search.main([]) == 0

    reported = capsys.readouterr().out
    judged = reported.split("open this to judge it: ")[1].splitlines()[0]
    attached = reported.split("attach this one if you pick it: ")[1].splitlines()[0]
    assert judged == attached
    assert len(list((searching_agent / "media").glob("*.gif"))) == 1


def test_asks_for_no_more_than_the_ceiling(searching_agent, monkeypatch):
    seen = stub_klipy(monkeypatch, [gif_item()])

    generate_agent_gif_search.main(["--query", "cat", "--count", "40"])

    assert f"per_page={generate_agent_gif_search.MAX_COUNT}" in seen["searched"]


def test_says_so_when_the_search_finds_nothing(searching_agent, monkeypatch, capsys):
    stub_klipy(monkeypatch, [])

    assert generate_agent_gif_search.main(["--query", "asdfghjkl"]) == 1
    assert "asdfghjkl" in capsys.readouterr().err


def test_never_prints_the_key_back_out(searching_agent, monkeypatch, capsys):
    def refuse(url):
        raise MediaRequestRefused(f"provider refused {url}")

    monkeypatch.setattr(generate_agent_gif_search, "get_json", refuse)

    assert generate_agent_gif_search.main(["--query", "cat"]) == 1
    reported = capsys.readouterr().err
    assert "klipy-test" not in reported and "***" in reported


def test_refuses_once_the_day_is_spent(searching_agent, monkeypatch, capsys):
    stub_klipy(monkeypatch, [gif_item()])
    monkeypatch.setattr(generate_agent_gif_search, "DAILY_LIMIT", 1)

    assert generate_agent_gif_search.main(["--query", "cat"]) == 0
    assert generate_agent_gif_search.main(["--query", "cat"]) == 1
    assert "budget is spent" in capsys.readouterr().err


def test_refuses_when_every_candidate_is_too_big_to_send(
    searching_agent, monkeypatch, capsys
):
    stub_klipy(monkeypatch, [gif_item(sizes=(90_000_000,) * 4)])

    assert generate_agent_gif_search.main(["--query", "cat"]) == 1
    assert "too big to send" in capsys.readouterr().err


def test_a_machine_without_the_key_refuses_instead_of_crashing(
    searching_agent, media_secrets_directory, monkeypatch, capsys
):
    (media_secrets_directory / "klipy-api-key").unlink()
    stub_klipy(monkeypatch, [gif_item()])

    assert generate_agent_gif_search.main(["--query", "cat"]) == 1
    assert "klipy-api-key" in capsys.readouterr().err


def test_refuses_to_write_outside_an_agent_workspace(
    media_agent_workspace, monkeypatch
):
    monkeypatch.chdir(media_agent_workspace.parent)

    assert generate_agent_gif_search.main(["--query", "cat"]) == 1
