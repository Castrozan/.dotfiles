import logging
from pathlib import Path

import numpy as np
import onnxruntime as ort

logger = logging.getLogger(__name__)

SILERO_MODEL_URL = "https://github.com/snakers4/silero-vad/raw/master/src/silero_vad/data/silero_vad.onnx"
DEFAULT_MODEL_PATH = Path.home() / ".cache" / "voice-pipeline" / "silero_vad.onnx"


class SileroVad:
    def __init__(
        self,
        model_path: str = "",
        sample_rate: int = 16000,
    ) -> None:
        resolved_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        if not resolved_path.exists():
            self._download_model(resolved_path)

        self._session = ort.InferenceSession(
            str(resolved_path),
            providers=["CPUExecutionProvider"],
        )
        self._sample_rate = sample_rate
        self._h = np.zeros((2, 1, 64), dtype=np.float32)
        self._c = np.zeros((2, 1, 64), dtype=np.float32)
        logger.info("Silero VAD loaded from %s", resolved_path)

    def process_frame(self, audio_frame: bytes) -> float:
        audio = np.frombuffer(audio_frame, dtype=np.int16).astype(np.float32) / 32767.0
        audio = audio[np.newaxis, :]

        ort_inputs = {
            "input": audio,
            "h": self._h,
            "c": self._c,
            "sr": np.array([self._sample_rate], dtype=np.int64),
        }

        output, self._h, self._c = self._session.run(None, ort_inputs)
        return float(output[0][0])

    def reset(self) -> None:
        self._h = np.zeros((2, 1, 64), dtype=np.float32)
        self._c = np.zeros((2, 1, 64), dtype=np.float32)

    @staticmethod
    def _download_model(target: Path) -> None:
        import urllib.request
        target.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Downloading Silero VAD model to %s", target)
        urllib.request.urlretrieve(SILERO_MODEL_URL, str(target))
        logger.info("Silero VAD model downloaded")
