import math

import numpy

SAMPLE_RATE = 16000
FFT_SIZE = 400
HOP_LENGTH = 160
MEL_BANDS = 80
SLANEY_LINEAR_LIMIT_HERTZ = 1000.0
SLANEY_LINEAR_LIMIT_MEL = 15.0
SLANEY_LOG_STEP = 27.0 / math.log(6.4)


def hertz_to_mel(hertz):
    if hertz < SLANEY_LINEAR_LIMIT_HERTZ:
        return 3.0 * hertz / 200.0
    return (
        SLANEY_LINEAR_LIMIT_MEL
        + math.log(hertz / SLANEY_LINEAR_LIMIT_HERTZ) * SLANEY_LOG_STEP
    )


def mel_to_hertz(mels):
    linear = 200.0 * mels / 3.0
    logarithmic = SLANEY_LINEAR_LIMIT_HERTZ * numpy.exp(
        (mels - SLANEY_LINEAR_LIMIT_MEL) / SLANEY_LOG_STEP
    )
    return numpy.where(mels >= SLANEY_LINEAR_LIMIT_MEL, logarithmic, linear)


def slaney_mel_filters():
    frequency_bins = numpy.linspace(0, SAMPLE_RATE // 2, 1 + FFT_SIZE // 2)
    band_edges = mel_to_hertz(
        numpy.linspace(0.0, hertz_to_mel(SAMPLE_RATE / 2), MEL_BANDS + 2)
    )
    edge_widths = numpy.diff(band_edges)
    slopes = band_edges[None, :] - frequency_bins[:, None]
    rising = -slopes[:, :-2] / edge_widths[:-1]
    falling = slopes[:, 2:] / edge_widths[1:]
    filters = numpy.maximum(0, numpy.minimum(rising, falling))
    return filters * (2.0 / (band_edges[2:] - band_edges[:-2]))[None, :]


MEL_FILTERS = slaney_mel_filters()
WINDOW = numpy.hanning(FFT_SIZE + 1)[:-1]


def log_mel_features(audio):
    normalized = (audio - audio.mean()) / numpy.sqrt(audio.var() + 1e-7)
    padded = numpy.pad(normalized, FFT_SIZE // 2, mode="reflect")
    frame_count = 1 + (len(padded) - FFT_SIZE) // HOP_LENGTH
    frames = numpy.lib.stride_tricks.sliding_window_view(padded, FFT_SIZE)[
        ::HOP_LENGTH
    ][:frame_count]
    power = numpy.abs(numpy.fft.rfft(frames * WINDOW, n=FFT_SIZE)) ** 2
    mel = numpy.maximum(1e-10, power @ MEL_FILTERS).T
    log_mel = numpy.log10(mel)[:, :-1]
    log_mel = numpy.maximum(log_mel, log_mel.max() - 8.0)
    return ((log_mel + 4.0) / 4.0).astype(numpy.float32)[None, :, :]
