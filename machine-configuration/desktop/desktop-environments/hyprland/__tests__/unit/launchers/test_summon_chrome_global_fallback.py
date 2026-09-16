import summon_chrome_global as summoner


def test_finds_standard_window_when_tag_and_titles_do_not_match(
    mock_subprocess_run, hyprctl_response_builder
):
    hyprctl_response_builder(
        "clients",
        [
            {
                "class": "chrome-global",
                "address": "0xc",
                "tags": [],
                "title": "WhatsApp - Google Chrome",
                "initialTitle": "Everything F1 is banning in 2027 - YouTube - Google Chrome",
                "floating": False,
                "workspace": {"id": 1},
            }
        ],
    )

    result = summoner.find_chrome_global_main_window()

    assert result["address"] == "0xc"
    tag_calls = [
        call for call in mock_subprocess_run.call_args_list if "tagwindow" in str(call)
    ]
    assert tag_calls
