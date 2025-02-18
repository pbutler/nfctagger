"""
This is the chipset underlying the ACR122U device and mant other NFC
devices.

More info:
https://www.nxp.com/docs/en/user-guide/157830_PN533_um080103.pdf
"""
from construct import Bytes
from construct import Const
from construct import GreedyBytes
from construct import Struct

from . import ParentDevice
from ..data import Command
from ..data import Response
from .ntag import NTag

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
    """Tunneling command, with constant header"""
    def _struct(self):
        return Struct(
            "header" / Const(b"\xd4\x42"),
            "data_out" / GreedyBytes,  # pyright: ignore
        )

    def validate(self):
        """ Validate data_out field, which as the docs says must be less than 264 bytes"""
        #TODO: Hook this in
        if len(self._data.data_out) < 264:
            raise ValueError("data_out must be less than 264 bytes")

    def child(self) -> bytes:
        """Return the data_out field"""
        return self._data.data_out.build()


class PN53x(ParentDevice):

    possible_children = [NTag, ]

    def __init__(self, connection):
        super().__init__(connection)

    @classmethod
    def identify(cls, parent):
        #TODO: Implement actual identification
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
