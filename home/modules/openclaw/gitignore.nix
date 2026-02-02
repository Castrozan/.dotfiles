{ config, ... }:
{
  home.file."${config.openclaw.workspacePath}/.gitignore".text = ''
    node_modules/
    venv-*/
    __pycache__/
    *.pyc
    *.log
    dist/
    .devenv/
    /package.json
    /package-lock.json
    *.key
    *.pem
    .env
    .clawhub/
    .DS_Store
    *.tmp
    .vscode/
    .idea/
  '';
}
