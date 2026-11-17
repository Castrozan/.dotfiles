import array

SAMPLE_TYPE = "h"


class LinearResampler:
    def __init__(self, source_rate, target_rate):
        self.source_rate = source_rate
        self.target_rate = target_rate
        self.position = 0
        self.carry = array.array(SAMPLE_TYPE)

    def resample(self, pcm):
        incoming = array.array(SAMPLE_TYPE)
        incoming.frombytes(pcm)
        samples = self.carry + incoming
        if not samples:
            return b""
        last = len(samples) - 1
        limit = last * self.target_rate
        resampled = array.array(SAMPLE_TYPE)
        position = self.position
        while position < limit:
            index, remainder = divmod(position, self.target_rate)
            first, second = samples[index], samples[index + 1]
            resampled.append(first + (second - first) * remainder // self.target_rate)
            position += self.source_rate
        self.position = position - limit
        self.carry = samples[last:]
        return resampled.tobytes()
