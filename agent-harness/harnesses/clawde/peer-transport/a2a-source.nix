{ pkgs, inputs }:
pkgs.applyPatches {
  name = "clawde-a2a-peer-delivery";
  src = "${inputs.clawde}/module/peer-adapters/a2a";
  patches = [ ./patches/a2a-peer-delivery.patch ];
  postPatch = ''
    cp ${../scripts/peer_notification_mailbox.py} a2a_server/peer_notification_mailbox.py
    cp ${../scripts/herdr_prompt_adapter.py} a2a_server/herdr_prompt_adapter.py
  '';
}
