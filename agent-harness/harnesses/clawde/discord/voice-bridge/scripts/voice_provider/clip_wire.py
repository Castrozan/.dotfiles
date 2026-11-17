import asyncio

MAXIMUM_CLIP_BYTES = 64 * 1024 * 1024
MAXIMUM_CLIP_SAMPLE_RATE = 192000
CLIP_UPLOAD_TIMEOUT_SECONDS = 30
BYTES_PER_MONO_SAMPLE = 2


def is_bounded_integer(value, maximum):
    return type(value) is int and 0 < value <= maximum


async def read_clip(request, reader):
    sample_rate = request["sample_rate"]
    byte_count = request["byte_count"]
    if not is_bounded_integer(sample_rate, MAXIMUM_CLIP_SAMPLE_RATE):
        raise ValueError("invalid_sample_rate")
    if not is_bounded_integer(byte_count, MAXIMUM_CLIP_BYTES):
        raise ValueError("invalid_byte_count")
    if byte_count % BYTES_PER_MONO_SAMPLE:
        raise ValueError("invalid_byte_count")
    pcm = await asyncio.wait_for(
        reader.readexactly(byte_count), timeout=CLIP_UPLOAD_TIMEOUT_SECONDS
    )
    return pcm, sample_rate
