from pathlib import Path

GPT_PROXY_MODULE = Path(__file__).resolve().parents[2] / "default.nix"


def module_source() -> str:
    return GPT_PROXY_MODULE.read_text()


def test_the_served_configuration_points_the_proxy_at_a_gateway_url():
    assert 'proxy-url: "${outboundProxyUrlForGatewayPort ipv4GatewayPort}"' in (
        module_source()
    ), (
        "cli-proxy-api only sends its upstream traffic through the gateway when its "
        "configuration carries proxy-url, so dropping that line puts every request "
        "back on whichever address family the resolver prefers"
    )


def test_both_the_service_and_the_login_run_through_the_gateway():
    source = module_source()

    assert "ipv4GatewayCliProxyApiProgramArguments" in source
    assert "ipv4GatewayCliProxyApiLoginProgramArguments" in source
    assert (
        "${lib.escapeShellArgs ipv4GatewayCliProxyApiLoginProgramArguments}" in source
    ), (
        "the OAuth exchange reaches the same upstream as the served requests, so a "
        "login left off the gateway fails on a host with unusable IPv6 while the "
        "service beside it works"
    )


def test_the_login_gateway_listens_on_its_own_port():
    assert "proxyIpv4GatewayLoginPort = 8319;" in module_source(), (
        "the login runs while the service is already listening, so sharing one "
        "gateway port makes claude-gpt-login fail to bind"
    )
