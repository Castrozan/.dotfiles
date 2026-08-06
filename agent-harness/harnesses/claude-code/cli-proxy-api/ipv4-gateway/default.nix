{ pkgs }:
let
  ipv4GatewaySource = pkgs.writeText "cli-proxy-api-ipv4-gateway.py" (
    builtins.readFile ./scripts/cli_proxy_api_ipv4_gateway.py
  );
in
{
  outboundProxyUrlFor =
    { listenAddress, listenPort }: "http://${listenAddress}:${toString listenPort}";

  programArgumentsThroughIpv4Gateway =
    {
      listenAddress,
      listenPort,
      programArguments,
    }:
    [
      "${pkgs.python312}/bin/python3"
      "${ipv4GatewaySource}"
      listenAddress
      (toString listenPort)
    ]
    ++ programArguments;
}
