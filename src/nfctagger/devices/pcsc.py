from loguru import logger

from construct import Struct, GreedyBytes

from . import ParentDevice, Tag
from .acr122 import ACR122U

from ..data import Response, Command


class PCSCResp(Response):
    def _struct(self):
        return Struct(
            "data_out" / GreedyBytes,  # pyright: ignore
        )

    def child(self):
        return self._data.data_out


class PCSC(ParentDevice):
    possible_children = (ACR122U,)

    def __init__(self, connection):
        super().__init__(connection)

    def write(self, cmd: Command, tunnel=False) -> Response:
        # logger.debug(f"> {cmd}")
        response, sw1, sw2 = self._connection.transmit(list(cmd.bytes()))
        assert sw1 == 0x90 and sw2 == 0x00
        # logger.debug(
        #    f"< {' '.join(f'{byte:02X}' for byte in response)}, SW1: {sw1:02X}, SW2: {sw2:02X}"
        # )
        return PCSCResp(bdata=bytearray(response))

    def get_tag(self) -> Tag:
        cur = self
        while hasattr(cur, "_child"):
            cur = cur._child
            assert cur is not None
        assert isinstance(cur, Tag)
        return cur
