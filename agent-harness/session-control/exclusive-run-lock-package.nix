{ pkgs }:
pkgs.runCommand "exclusive-run-lock" { } ''
  mkdir -p $out/libexec/exclusive-run-lock/agent_session
  install -m 0644 ${./.}/exclusive-run-lock.sh $out/libexec/exclusive-run-lock/exclusive-run-lock.sh
  install -m 0644 ${./.}/exclusive_run_lock.py $out/libexec/exclusive-run-lock/exclusive_run_lock.py
  install -m 0644 ${./.}/exclusive_run_scope.py $out/libexec/exclusive-run-lock/exclusive_run_scope.py
  install -m 0644 ${./.}/exclusive_run_owner.py $out/libexec/exclusive-run-lock/exclusive_run_owner.py
  install -m 0644 ${./.}/exclusive_run_diagnostics.py $out/libexec/exclusive-run-lock/exclusive_run_diagnostics.py
  install -m 0644 ${./agent_session}/harness.py ${./agent_session}/processes.py $out/libexec/exclusive-run-lock/agent_session/
  substituteInPlace $out/libexec/exclusive-run-lock/exclusive-run-lock.sh \
    --replace-fail 'python3 ' '${pkgs.python312}/bin/python3 '
''
