import json
import math
import os
import re
import sys
from pathlib import Path

import speech_segmenter

MODEL_ENVIRONMENT_VARIABLE = "AVATAR_SPEAKER_MODEL"
MATCH_THRESHOLD = 0.55
MINIMUM_ENROLLMENT_EMBEDDINGS = 3
PROFILE_NAME = re.compile(r"[A-Za-z0-9_-]+")


def voices_directory():
    base = os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state"
    return Path(base) / "avatar" / "voices"


def validated_name(name):
    if not PROFILE_NAME.fullmatch(name):
        raise ValueError("Voice names may only use letters, digits, _ and -")
    return name


def cosine_similarity(first, second):
    if len(first) != len(second):
        return 0.0
    norms = math.hypot(*first) * math.hypot(*second)
    if not norms:
        return 0.0
    return sum(a * b for a, b in zip(first, second, strict=True)) / norms


def unit_vector(vector):
    norm = math.hypot(*vector)
    return [value / norm for value in vector] if norm else list(vector)


def mean_vector(vectors):
    return [sum(values) / len(vectors) for values in zip(*vectors, strict=True)]


class VoiceProfiles:
    def __init__(self, directory):
        self.directory = directory

    def path(self, name):
        return self.directory / f"{validated_name(name)}.json"

    def names(self):
        if not self.directory.exists():
            return []
        return sorted(path.stem for path in self.directory.glob("*.json"))

    def load(self, name):
        path = self.path(name)
        return json.loads(path.read_text()) if path.exists() else None

    def save(self, name, embedding, samples):
        path = self.path(name)
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "w") as output:
            json.dump({"embedding": embedding, "samples": samples}, output)
        os.replace(temporary, path)

    def forget(self, name):
        path = self.path(name)
        if not path.exists():
            raise ValueError(f"No voice named {name}")
        path.unlink()

    def best_match(self, embedding):
        best_name, best_score = None, MATCH_THRESHOLD
        for name in self.names():
            score = cosine_similarity(embedding, self.load(name)["embedding"])
            if score > best_score:
                best_name, best_score = name, score
        return best_name


def append_embedding(path, sequence, embedding):
    descriptor = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(descriptor, "a") as output:
        output.write(json.dumps({"sequence": sequence, "embedding": embedding}) + "\n")


def read_embeddings(path, first, last):
    if not path.exists():
        return []
    entries = (json.loads(line) for line in path.read_text().splitlines())
    return [
        entry["embedding"] for entry in entries if first <= entry["sequence"] <= last
    ]


def enroll(profiles, embeddings_path, name, first, last):
    validated_name(name)
    embeddings = read_embeddings(embeddings_path, first, last)
    if len(embeddings) < MINIMUM_ENROLLMENT_EMBEDDINGS:
        raise ValueError(
            f"Enrolling needs at least {MINIMUM_ENROLLMENT_EMBEDDINGS} segments, "
            f"found {len(embeddings)} between {first} and {last}"
        )
    vectors = [unit_vector(embedding) for embedding in embeddings]
    existing = profiles.load(name)
    if existing and len(existing["embedding"]) == len(vectors[0]):
        vectors += [existing["embedding"]] * existing["samples"]
        samples = len(embeddings) + existing["samples"]
    else:
        samples = len(embeddings)
    profiles.save(name, mean_vector(vectors), samples)
    return samples


def sherpa_extractor(model_path):
    import numpy
    import sherpa_onnx

    extractor = sherpa_onnx.SpeakerEmbeddingExtractor(
        sherpa_onnx.SpeakerEmbeddingExtractorConfig(model=model_path, num_threads=1)
    )

    def embed(segment):
        samples = numpy.frombuffer(segment, dtype=numpy.int16).astype(numpy.float32)
        stream = extractor.create_stream()
        stream.accept_waveform(speech_segmenter.SAMPLE_RATE, samples / 32768)
        stream.input_finished()
        return [float(value) for value in extractor.compute(stream)]

    return embed


class SpeakerIdentifier:
    def __init__(self, model_path, profiles, load_extractor=sherpa_extractor):
        self.model_path = model_path
        self.profiles = profiles
        self.load_extractor = load_extractor
        self.embed = None
        self.unavailable = False

    def available(self):
        if self.embed or self.unavailable:
            return bool(self.embed)
        try:
            if not self.model_path:
                raise RuntimeError(f"{MODEL_ENVIRONMENT_VARIABLE} is not set")
            self.embed = self.load_extractor(self.model_path)
        except Exception as error:
            self.unavailable = True
            print(f"Speaker identity is off: {error}", file=sys.stderr)
        return bool(self.embed)

    def identify(self, segment):
        if not self.available():
            return None, None
        try:
            embedding = self.embed(segment)
            return self.profiles.best_match(embedding), embedding
        except Exception as error:
            print(f"Speaker identity failed for a segment: {error}", file=sys.stderr)
            return None, None


class DisabledIdentifier:
    def identify(self, segment):
        return None, None


def configured_identifier(enabled):
    if not enabled:
        return DisabledIdentifier()
    return SpeakerIdentifier(
        os.environ.get(MODEL_ENVIRONMENT_VARIABLE), VoiceProfiles(voices_directory())
    )
