#!/usr/bin/env python3
"""Run a workspace-local Nix installation without modifying the host root.

The synthetic root mirrors the existing sandbox read-only. Only this dedicated
workspace tree is writable; pre-existing sandbox restrictions remain inherited.
"""
import os
import pathlib
import pwd
import sys

source = pathlib.Path(__file__).resolve().parent
root = pathlib.Path(os.environ.get("DOT_ROOT", source.parent / ".runtime")).expanduser().resolve()
if root == source or root in source.parents:
    sys.exit("DOT_ROOT must not contain the source checkout")
for part in ('store', 'home', 'tmp', 'config/nix'):
    (root / part).mkdir(parents=True, exist_ok=True)
args = ['bwrap', '--unshare-user', '--unshare-pid', '--die-with-parent', '--tmpfs', '/']
for name in sorted(os.listdir('/')):
    path = '/' + name
    if name in ('nix', 'tmp', 'dev', 'proc'):
        continue
    if os.path.islink(path):
        args += ['--symlink', os.readlink(path), path]
    elif os.path.isdir(path) or os.path.isfile(path):
        args += ['--ro-bind', path, path]
args += ['--dev', '/dev', '--proc', '/proc', '--bind', str(root), str(root), '--bind', str(root / 'store'), '/nix',
         '--bind', str(root / 'tmp'), '/tmp', '--remount-ro', '/',
         '--setenv', 'USER', pwd.getpwuid(os.getuid()).pw_name,
         '--setenv', 'LOGNAME', pwd.getpwuid(os.getuid()).pw_name,
         '--setenv', 'HOME', str(root / 'home'),
         '--setenv', 'XDG_CONFIG_HOME', str(root / 'home/.config'),
         '--setenv', 'XDG_CACHE_HOME', str(root / 'home/.cache'),
         '--setenv', 'XDG_STATE_HOME', str(root / 'home/.local/state'),
         '--setenv', 'NIX_CONF_DIR', str(root / 'config/nix'),
         '--setenv', 'PATH', str(root / 'home/.nix-profile/bin') + ':' + os.environ.get('PATH', '/usr/bin:/bin'),
         '--chdir', str(source), '--']
args += sys.argv[1:] or ['/bin/bash']
os.execvp(args[0], args)
