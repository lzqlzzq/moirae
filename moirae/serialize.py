import msgpack
import lz4.frame


def serialize(data):
    serialized = msgpack.packb(data)
    compressed = lz4.frame.compress(serialized)

    return compressed


def deserialize(data: bytes):
    decompressed = lz4.frame.decompress(data)
    obj = msgpack.unpackb(decompressed)

    return obj
