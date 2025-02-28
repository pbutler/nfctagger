import construct as c
from construct import this

from .data import Frame


class TLengthV(c.Construct):
    def _parse(self, stream, context, path):
        b = c.byte2int(c.stream_read(stream, 1, path))
        if b == 0xFF:
            b2 = c.stream_read(stream, 1, path)
            b3 = c.stream_read(stream, 1, path)
            b = ((c.byte2int(b2) & 0xFF) << 8) | (c.byte2int(b3) & 0xFF)
        return b

    def _build(self, obj, stream, context, path):
        B = bytearray()
        if obj >= 0xFF:
            B.append(0xFF)
            B.append((obj >> 8) & 0xFF)
            B.append(obj & 0xFF)
        else:
            B.append(obj & 0xFF)
        c.stream_write(stream, bytes(B), len(B), path)
        return obj

    def _sizeof(self, context, path):
        raise c.SizeofError(
            "TLengthV is variable sized"
        )  # (when variable size or unknown)


class NDEF_TLV(Frame):
    """
    TLV structure that automatically calculates the length of the value
    and appends the 0xfe terminator.
    """
    def __init__(self, bdata=None, data=None):
        super().__init__(bdata=bdata, data=data)
        if "length" not in self._data:
            self._data["length"] = len(self._data["value"])

        assert self._data["length"] == len(self._data["value"])

    def _struct(self):
        return c.Struct(
            "type" / c.Const(b"\x03"),
            "length" / c.Rebuild(TLengthV(), c.len_(this.value)),
            "value" / c.NullTerminated(c.GreedyBytes, term=b"\xfe"),
        )
