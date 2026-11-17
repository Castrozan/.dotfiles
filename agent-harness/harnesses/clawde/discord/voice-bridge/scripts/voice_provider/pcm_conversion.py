from array import array

SAMPLES_AVERAGED_PER_OUTPUT_SAMPLE = 3
STEREO_CHANNELS = 2


def samples_from_pcm(pcm):
    samples = array("h")
    samples.frombytes(pcm[: len(pcm) - len(pcm) % samples.itemsize])
    return samples


def mono_from_stereo(samples):
    return array(
        "h",
        (
            (left + right) >> 1
            for left, right in zip(samples[0::2], samples[1::2], strict=False)
        ),
    )


def averaged_in_threes(samples):
    third = SAMPLES_AVERAGED_PER_OUTPUT_SAMPLE
    return array(
        "h",
        (
            sum(group) // third
            for group in zip(
                samples[0::third], samples[1::third], samples[2::third], strict=False
            )
        ),
    )


def mono_pcm_from_interleaved(pcm, channels):
    samples = samples_from_pcm(pcm)
    if channels == STEREO_CHANNELS:
        samples = mono_from_stereo(samples)
    return samples.tobytes()


def capture_pcm_from_discord_pcm(pcm):
    return averaged_in_threes(mono_from_stereo(samples_from_pcm(pcm))).tobytes()
