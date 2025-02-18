from logging import getLogger

from construct import Struct, Const, Prefixed, Int8ul, GreedyBytes

from . import ParentDevice
from .pn53x import PN53x

from ..data import Response, Command

log = getLogger(__name__)


class ACR122DirectTransmitCmd(Command):
    def _struct(self):
        return Struct(
            "header" / Const(b"\xff\x00\x00\x00"),
            "data_in" / Prefixed(Int8ul, GreedyBytes),
        )

    def child(self):
        return self._data.data_in


class ACR122DirectTransmitResp(Response):
    def _struct(self):
        return Struct(
            "data_out" / GreedyBytes,  # pyright: ignore
        )

    def child(self):
        return self._data.data_out


class ACR122U(ParentDevice):
    possible_children = (PN53x,)

    @classmethod
    def identify(cls, connection):
        return True

    def write(self, cmd: Command, tunnel=False) -> Response:
        if tunnel:
            tframe = ACR122DirectTransmitCmd(data={"data_in": cmd.bytes()})
            response = self._connection.write(tframe, tunnel=True)
            response = ACR122DirectTransmitResp(bdata=response.child())
            return response
        else:
            response = self._connection.write(cmd)
            return response
