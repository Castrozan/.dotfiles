from speech_segmenter import SAMPLE_RATE

MODEL_ENVIRONMENT_VARIABLE = "AVATAR_TURN_MODEL"
TURN_SECONDS = 8
TURN_BYTES = TURN_SECONDS * SAMPLE_RATE * 2
FINISHED_PROBABILITY = 0.5


class SmartTurnDetector:
    def __init__(self, model_path):
        import numpy
        import onnxruntime
        from transformers import WhisperFeatureExtractor

        options = onnxruntime.SessionOptions()
        options.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL
        options.inter_op_num_threads = 1
        self.numpy = numpy
        self.session = onnxruntime.InferenceSession(model_path, sess_options=options)
        self.features = WhisperFeatureExtractor(chunk_length=TURN_SECONDS)

    def finished(self, pcm):
        samples = self.numpy.frombuffer(pcm, dtype=self.numpy.int16)[-TURN_BYTES // 2 :]
        audio = samples.astype(self.numpy.float32) / 32768
        audio = self.numpy.pad(audio, (TURN_BYTES // 2 - len(audio), 0))
        features = self.features(
            audio,
            sampling_rate=SAMPLE_RATE,
            return_tensors="np",
            padding="max_length",
            max_length=TURN_BYTES // 2,
            truncation=True,
            do_normalize=True,
        ).input_features.astype(self.numpy.float32)
        probability = self.session.run(None, {"input_features": features})[0][0].item()
        return probability > FINISHED_PROBABILITY


class TurnTracker:
    def __init__(self, finished):
        self.finished = finished
        self.audio = bytearray()

    def add(self, segment):
        self.audio += segment
        del self.audio[:-TURN_BYTES]
        if not self.finished(bytes(self.audio)):
            return False
        self.audio.clear()
        return True
