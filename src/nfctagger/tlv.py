from construct import Construct, Struct, Const, Byte, NullTerminated, GreedyBytes
from construct import stream_read, stream_write
from construct import byte2int
from construct import SizeofError
from construct import Rebuild, this, len_


class TLengthV(Construct):
    def _parse(self, stream, context, path):
        b = byte2int(stream_read(stream, 1, path))
        if b == 0xFF:
            b2 = stream_read(stream, 1, path)
            b3 = stream_read(stream, 1, path)
            b = ((byte2int(b2) & 0xFF) << 8) | (byte2int(b3) & 0xFF)
        return b

    def _build(self, obj, stream, context, path):
        B = bytearray()
        if obj >= 0xFF:
            B.append(0xFF)
            B.append((obj >> 8) & 0xFF)
            B.append(obj & 0xFF)
        else:
            B.append(obj & 0xFF)
        stream_write(stream, bytes(B), len(B), path)
        return obj

    def _sizeof(self, context, path):
        raise SizeofError(
            "TLengthV is variable sized"
        )  # (when variable size or unknown)


def NDEF_TLV() -> Struct:
    return Struct(
        "type" / Const(b"\x03"),
        "length" / Rebuild(TLengthV(), len_(this.value)),
        "value" / NullTerminated(GreedyBytes, term=b"\xfe"),
    )


if __name__ == "__main__":
    tlv = NDEF_TLV()
    short = tlv.build({"value": bytearray(0x01 for _ in range(10))})
    long = tlv.build({"value": bytearray(0x01 for _ in range(260))})
    print(tlv.parse(b"\x03\x01\x01\xfe"))
    print(tlv.parse(short))
    print(short)
    assert len(short) == 13
    print(tlv.parse(long))
    assert len(long) == 265
    print(long)
