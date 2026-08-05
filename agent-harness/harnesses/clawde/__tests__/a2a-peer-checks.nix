{
  lib,
  mkEvalCheck,
  helpers,
  self,
  ...
}:
let
  fleetWithTwoAgents = helpers.homeManagerTestConfiguration [
    self.homeManagerModules.clawde
    self.homeManagerModules.claude-code
    {
      clawde.multiplexer = "herdr";
      clawde.agents = {
        agent-that-describes-itself = {
          harness = "claude";
          personality = "Agent carrying an a2a description";
          expose.a2a.agentDescriptionForCard = "does the thing a caller routes to";
        };
        agent-that-describes-nothing = {
          harness = "claude";
          personality = "Agent carrying no a2a description";
        };
      };
    }
  ];

  supervisedWindows = (builtins.head fleetWithTwoAgents.clawde.serviceSpecification.sessions).agents;

  inherit (fleetWithTwoAgents.clawde.a2a) agentMetadata;

  daemonExecStart = toString fleetWithTwoAgents.systemd.user.services.clawde-a2a.Service.ExecStart;
in
{
  clawde-the-a2a-daemon-never-takes-a-window-from-an-agent =
    mkEvalCheck "clawde-the-a2a-daemon-never-takes-a-window-from-an-agent"
      (
        map (window: window.name) supervisedWindows == [
          "agent-that-describes-itself"
          "agent-that-describes-nothing"
        ]
        && lib.all (window: window.sidecar_processes == [ ]) supervisedWindows
      )
      "one daemon serves the whole machine, so nothing a2a may hang off an individual agent: a per-agent window puts every exposed agent in the tab bar twice, and a per-agent sidecar brings back the process-per-pane poll rate that made the daemon worth building";

  clawde-the-a2a-daemon-runs-for-the-whole-machine-on-one-port =
    mkEvalCheck "clawde-the-a2a-daemon-runs-for-the-whole-machine-on-one-port"
      (
        lib.hasInfix "--listen-port 7000" daemonExecStart
        && lib.hasInfix "--listen-host 127.0.0.1" daemonExecStart
      )
      "the daemon is the only thing listening, and it listens on loopback: a per-agent port would have to be allocated for sessions nobody declared, and a non-loopback bind hands every host on the LAN a keyboard into every live agent session on this machine";

  clawde-an-agent-reaches-the-daemon-through-its-description-not-a-toggle =
    mkEvalCheck "clawde-an-agent-reaches-the-daemon-through-its-description-not-a-toggle"
      (
        agentMetadata.agents.agent-that-describes-itself.description == "does the thing a caller routes to"
        && agentMetadata.agents.agent-that-describes-nothing.description == ""
      )
      "an agent is reachable because it is a running pane, never because it opted in, so this metadata may only carry what a caller could not discover: the moment a description doubles as an enable flag, an agent that set none stops answering";

  clawde-the-daemon-is-told-how-to-read-every-harness-it-may-meet =
    mkEvalCheck "clawde-the-daemon-is-told-how-to-read-every-harness-it-may-meet"
      (lib.all (harnessName: agentMetadata.harnessMeaningfulLinePatterns ? ${harnessName}) [
        "claude"
        "codex"
        "opencode"
      ])
      "the daemon attaches to panes running harnesses no clawde agent declares, and picks the pattern that isolates an answer from pane chrome by harness name; a harness missing here returns raw pane text as the agent's reply, spinner frames and all";
}
