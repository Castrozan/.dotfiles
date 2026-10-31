from control_server_node_runner import evaluate_node_json, requires_node


@requires_node
def test_output_target_excludes_the_local_control_window():
    result = evaluate_node_json(
        """
        const { ChromeDevtoolsTargetLocator } = require("./chrome-devtools/chrome-devtools-target-locator");
        const locator = new ChromeDevtoolsTargetLocator(9222);
        locator.get = async () => [
          {type: "page", url: "http://localhost:3000/controls.html", id: "controls"},
          {type: "page", url: "http://localhost:3000/?output=1", id: "output"},
        ];
        const result = locator.findPageTarget("localhost:3000/?output=1");
        """
    )
    assert result["id"] == "output"


@requires_node
def test_open_output_uses_chromes_encoded_new_target_query():
    result = evaluate_node_json(
        """
        const { ChromeDevtoolsTargetLocator } = require("./chrome-devtools/chrome-devtools-target-locator");
        const locator = new ChromeDevtoolsTargetLocator(9222);
        locator.put = async route => route;
        const result = locator.openTab("http://localhost:3000/?output=1&view=side");
        """
    )
    assert (
        result
        == "/json/new?http%3A%2F%2Flocalhost%3A3000%2F%3Foutput%3D1%26view%3Dside"
    )
