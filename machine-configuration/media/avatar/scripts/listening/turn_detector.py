from speech_segmenter import SAMPLE_RATE

MODEL_ENVIRONMENT_VARIABLE = "AVATAR_TURN_MODEL"
TURN_SECONDS = 8
TURN_SAMPLES = TURN_SECONDS * SAMPLE_RATE
TURN_BYTES = TURN_SAMPLES * 2
FINISHED_PROBABILITY = 0.5


class SmartTurnDetector:
    def __init__(self, model_path):
        import numpy
        import onnxruntime
        import whisper_features

        options = onnxruntime.SessionOptions()
        options.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL
        options.inter_op_num_threads = 1
        self.numpy = numpy
        self.features = whisper_features.log_mel_features
        self.session = onnxruntime.InferenceSession(model_path, sess_options=options)

    def window(self, pcm):
        samples = self.numpy.frombuffer(pcm, dtype=self.numpy.int16)[-TURN_SAMPLES:]
        audio = samples.astype(self.numpy.float32) / 32768
        return self.numpy.pad(audio, (TURN_SAMPLES - len(audio), 0))

    def probability(self, pcm):
        features = self.features(self.window(pcm))
        return self.session.run(None, {"input_features": features})[0][0].item()

    def finished(self, pcm):
        return self.probability(pcm) > FINISHED_PROBABILITY


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
