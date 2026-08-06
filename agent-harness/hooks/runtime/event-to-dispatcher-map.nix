{
  dispatchersByEvent = {
    PreToolUse = "pre-tool-use-dispatcher.py";
    PostToolUse = "post-tool-use-dispatcher.py";
    SessionStart = "session-start-dispatcher.py";
    Stop = "stop-dispatcher.py";
    SubagentStop = "stop-dispatcher.py";
  };
  inlineExceptionEvents = [ "PermissionRequest" ];
}
