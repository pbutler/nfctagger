from logging import getLogger

from ..data import Response, Command
from construct import Struct, Bytes, GreedyBytes, Const
from . import ParentDevice
from .ntag import NTag

log = getLogger(__name__)


class PN53xInCommunicateThruResp(Response):
    def _struct(self):
        return Struct(
            "header" / Bytes(2) * "0xD5 0x43",
            "status" / Bytes(1),
            "data_in" / GreedyBytes,  # pyright: ignore
        )

    def child(self):
        assert self._data is not None
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


class PN53x(ParentDevice):
    possible_children = (NTag,)

    def __init__(self, connection):
        super().__init__(connection)

    @classmethod
    def identify(cls, connection):
        return True

    def write(self, cmd: Command, tunnel=False) -> Response:
        if tunnel:
            tframe = PN53xInCommunicateThruCmd(data={"data_out": cmd.bytes()})
            response = self._connection.write(tframe, tunnel=True)
            bresp = response.child()
            response = PN53xInCommunicateThruResp(bdata=bresp)
            return response
        else:
            response = self._connection.write(cmd)
            return response
