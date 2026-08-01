{
  lib,
  mkEvalCheck,
  helpers,
  self,
}:
let
  fleetExposingOneAgentAsAPeer = helpers.homeManagerTestConfiguration [
    self.homeManagerModules.clawde
    self.homeManagerModules.claude-code
    {
      clawde.multiplexer = "herdr";
      clawde.agents = {
        agent-reachable-over-a2a = {
          harness = "claude";
          personality = "Agent exposed as an A2A peer";
          expose.a2a.enable = true;
          expose.a2a.listenPort = 7101;
        };
        agent-not-reachable-over-a2a = {
          harness = "claude";
          personality = "Agent with no peer exposure";
        };
      };
    }
  ];

  supervisedWindows =
    (builtins.head fleetExposingOneAgentAsAPeer.clawde.serviceSpecification.sessions).agents;

  windowNamed =
    agentName: builtins.head (builtins.filter (window: window.name == agentName) supervisedWindows);

  sidecarProcessNamesOf =
    agentName: map (sidecar: sidecar.name) (windowNamed agentName).sidecar_processes;

  peerCommandOf = agentName: (builtins.head (windowNamed agentName).sidecar_processes).command;
in
{
  clawde-an-a2a-peer-never-takes-a-window-of-its-own =
    mkEvalCheck "clawde-an-a2a-peer-never-takes-a-window-of-its-own"
      (
        map (window: window.name) supervisedWindows == [
          "agent-not-reachable-over-a2a"
          "agent-reachable-over-a2a"
        ]
      )
      "the peer is plumbing rather than something a human opens, so it runs headless beside its agent: give it a window and every exposed agent shows up twice in the tab bar, and the window-reconcile loop retypes the peer command into a busy pane on every poll because no agent wrapper is running in it";

  clawde-an-a2a-peer-is-a-sidecar-of-the-agent-it-wraps =
    mkEvalCheck "clawde-an-a2a-peer-is-a-sidecar-of-the-agent-it-wraps"
      (
        sidecarProcessNamesOf "agent-reachable-over-a2a" == [ "agent-reachable-over-a2a-a2a" ]
        && sidecarProcessNamesOf "agent-not-reachable-over-a2a" == [ ]
      )
      "the supervisor only brings up a sidecar it can see on the agent it belongs to, and only while that agent should be running, so an exposed agent whose peer is not listed here is unreachable and an unexposed agent that grows one is serving a port nobody asked for";

  clawde-an-a2a-peer-attaches-through-the-live-multiplexer =
    mkEvalCheck "clawde-an-a2a-peer-attaches-through-the-live-multiplexer"
      (
        lib.hasInfix "--backend-type herdr" (peerCommandOf "agent-reachable-over-a2a")
        && lib.hasInfix "--herdr-tab-label agent-reachable-over-a2a" (
          peerCommandOf "agent-reachable-over-a2a"
        )
      )
      "the peer talks to the agent through whichever multiplexer actually hosts it, so a peer built for the wrong one starts, serves its port, accepts tasks and fails every single call against a target it can never find";

  clawde-an-a2a-peer-stays-findable-across-its-own-upgrades =
    mkEvalCheck "clawde-an-a2a-peer-stays-findable-across-its-own-upgrades"
      (
        !(lib.hasInfix "/nix/store/" (builtins.head (windowNamed "agent-reachable-over-a2a")
        .sidecar_processes).process_match_pattern)
      )
      "this pattern is the only way the supervisor recognises a peer it already started, so pinning it to the peer script's store path makes every edit to that script invisible to the reconcile loop and leaves the previous generation's peer holding the port the new one needs";
}
