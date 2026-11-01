import json
import subprocess
from pathlib import Path

RENDERER_DIRECTORY = Path(__file__).resolve().parents[2] / "renderer"


def run_renderer_module(module, body):
    program = f"""
    import("file://{RENDERER_DIRECTORY / module}").then(async (rendererModule) => {{
      {body}
    }}).catch(error => {{ console.error(error); process.exitCode = 1; }});
    """
    completed = subprocess.run(
        ["node", "-e", program], capture_output=True, text=True, check=True
    )
    return json.loads(completed.stdout)
