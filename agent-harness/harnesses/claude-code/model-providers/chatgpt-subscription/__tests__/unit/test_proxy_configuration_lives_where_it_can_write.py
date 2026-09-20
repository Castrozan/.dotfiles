from pathlib import Path

GPT_PROXY_MODULE = Path(__file__).resolve().parents[2] / "default.nix"


def module_source() -> str:
    return GPT_PROXY_MODULE.read_text()


def test_the_served_configuration_is_read_from_the_state_directory():
    source = module_source()

    assert 'proxyInstalledConfigurationPath = "${proxyStateDirectory}/config.yaml"' in (
        source
    )
    assert '"--config"\n    proxyInstalledConfigurationPath' in source, (
        "cli-proxy-api creates its management asset directory beside the file given "
        "to --config, so a /nix/store configuration makes it retry mkdir on a "
        "read-only path every three hours"
    )


def test_the_login_configuration_is_read_from_the_state_directory():
    source = module_source()

    assert (
        'proxyInstalledLoginConfigurationPath = "${proxyStateDirectory}/login-config.yaml"'
        in source
    )
    assert '"--config"\n          proxyInstalledLoginConfigurationPath' in source, (
        "claudex-login writes the same management asset, so leaving it on a store "
        "path fails the OAuth run on a host that has never authenticated"
    )


def test_activation_installs_both_configurations_as_owner_only_files():
    source = module_source()

    assert (
        "install -m 600 ${cliProxyApiConfigFile} ${lib.escapeShellArg proxyInstalledConfigurationPath}"
        in source
    )
    assert (
        "install -m 600 ${cliProxyApiLoginConfigFile} ${lib.escapeShellArg proxyInstalledLoginConfigurationPath}"
        in source
    ), (
        "the service reads the configuration at start, so activation must place a "
        "real writable-directory copy rather than leave the path missing"
    )
