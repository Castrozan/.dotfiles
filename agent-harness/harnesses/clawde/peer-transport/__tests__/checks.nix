{
  pkgs,
  lib,
  inputs,
  helpers,
  self,
  ...
}:
let
  transportSource = import ../a2a-source.nix { inherit pkgs inputs; };
  agentModules = [
    self.homeManagerModules.clawde
    self.homeManagerModules.claude-code
    {
      clawde.agents.transport-check = {
        harness = "claude";
        personality = "Transport check";
      };
    }
  ];
  linuxConfiguration = helpers.homeManagerTestConfiguration agentModules;
  darwinConfiguration = helpers.homeManagerTestConfigurationForDarwin agentModules;
  python = pkgs.python312.withPackages (packages: [ packages.pytest ]);
  harnessTests = "${self}/agent-harness/harnesses/clawde/__tests__";
  clientTests = "${self}/agent-harness/agent-to-agent-communication/client/__tests__/unit";
in
{
  clawde-a2a-linux-uses-the-owned-transport-source =
    helpers.mkEvalCheck "clawde-a2a-linux-uses-the-owned-transport-source"
      (
        lib.last linuxConfiguration.systemd.user.services.clawde-a2a.Service.Environment
        == "PYTHONPATH=${transportSource}"
      )
      "the daemon must import the patched live owner through its service environment";

  clawde-a2a-darwin-uses-the-owned-transport-source =
    helpers.mkEvalCheck "clawde-a2a-darwin-uses-the-owned-transport-source"
      (
        darwinConfiguration.launchd.agents.clawde-a2a.config.EnvironmentVariables.PYTHONPATH
        == "${transportSource}"
      )
      "the launch agent must import the same patched live owner";

  clawde-a2a-packaged-delivery-contract =
    pkgs.runCommandLocal "clawde-a2a-packaged-delivery-contract"
      {
        nativeBuildInputs = [ python ];
        CLAWDE_A2A_TRANSPORT_SOURCE = transportSource;
        PYTHONDONTWRITEBYTECODE = "1";
      }
      ''
        cd ${self}
        python -m pytest -q -p no:cacheprovider \
          ${harnessTests}/integration/test_harness_aware_submission.py \
          ${harnessTests}/integration/test_submission_observation.py \
          ${harnessTests}/integration/test_a2a_work_delivery.py \
          ${harnessTests}/integration/test_task_non_regression.py \
          ${harnessTests}/integration/test_a2a_mailbox_delivery.py \
          ${harnessTests}/integration/test_a2a_notification_requests.py \
          ${harnessTests}/integration/test_a2a_notification_commands.py \
          ${harnessTests}/unit/test_peer_notification_mailbox.py \
          ${clientTests}/test_a2a_cli_notifications.py \
          ${clientTests}/test_a2a_cli_peer_transport.py
        touch "$out"
      '';
}
