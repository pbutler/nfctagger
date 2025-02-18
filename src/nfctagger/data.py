from binascii import hexlify
from construct import (
    Struct,
    Bytes,
    Const,
    Container,
    GreedyBytes,
)
from construct.core import Construct


class Frame:
    def __init__(self, *, data=None, bdata=None):
        self._data: Container
        self._parser = self._struct()
        if data is not None:
            self._data = Container(data)
        elif bdata is not None:
            data = self._parser.parse(bdata)
            if data is None:
                raise ValueError("bdata could not be parsed")
            else:
                self._data = data
        else:
            raise ValueError("one of data and bdata must be defined")

    def _struct(self) -> Construct:
        return GreedyBytes  # pyright: ignore

    def bytes(self) -> bytes:
        return self._parser.build(self._data)

    def __len__(self):
        return len(self.bytes())

    def __str__(self):
        return f"<{self.__class__.__name__}: {self._data}>"


class Response(Frame):
    pass


class Command(Frame):
    pass


class PN53xInCommunicateThruResp(Response):
    def _struct(self):
        return Struct(
            "header" / Bytes(2) * "0xD5 0x43",
            "status" / Bytes(1),
            "data_in" / GreedyBytes,  # pyright: ignore
        )

    def child(self):
        return self._data.data_in


class PN53xInCommunicateThruCmd(Command):
    def _struct(self):
        return Struct(
            "header" / Const(b"\xd4\x42"),
            "data_out" / GreedyBytes,  # pyright: ignore
        )

    def validate(self):
        if len(self._data.data_out) > 264:
            raise ValueError("data_out must be less than 264 bytes")

    def child(self):
        return self._data.data_out.build()


if __name__ == "__main__":
    print(PN53xInCommunicateThruCmd(data={"data_out": b"\x01\x02\x03"}))
