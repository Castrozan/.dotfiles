import pathlib
import sys

AMBIENT_CANVAS_MEDIA_SCRIPTS_DIRECTORY = (
    pathlib.Path(__file__).resolve().parents[2] / "scripts" / "ambient_canvas_media"
)
sys.path.insert(0, str(AMBIENT_CANVAS_MEDIA_SCRIPTS_DIRECTORY))
