"""
ACS ACR122U device interface data structures

https://www.acs.com.hk/download-manual/419/API-ACR122U-2.04.pdf
"""
from construct import Const
from construct import GreedyBytes
from construct import Int8ul
from construct import Prefixed
from construct import Struct
from loguru import logger

from . import ParentDevice
from ..data import Command
from ..data import Response
from .pn53x import PN53x


class ACR122DirectTransmitCmd(Command):
    """Contains the header 0xff 0x00 0x00 0x00 and then the data to be sent"""

    def _struct(self):
        return Struct(
            "header" / Const(b"\xff\x00\x00\x00"),
            "data_in" / Prefixed(Int8ul, GreedyBytes),
        )

    def child(self):
        return self._data.data_in


class ACR122DirectTransmitResp(Response):
    """Response is just the response from the child device"""

    def _struct(self):
        return Struct(
            "data_out" / GreedyBytes,  # pyright: ignore
        )

    def child(self):
        return self._data.data_out


class ACR122U(ParentDevice):
    """
    ACR122U device object
    """

    possible_children = [
        PN53x,
    ]

    @classmethod
    def identify(cls, parent) -> bool:
        reader = parent._connection.getReader()
        logger.debug(f"Found Reader: {reader}")

        if "ACS ACR122U PICC" in reader:
            return True
        else:
            return False

    def write(self, cmd: Command, tunnel=False) -> Response:
        """
        If tunnel is True, the command will be sent to the child device
        by way for wrapping it in a ACR122DirectTransmitCmd frame
        """
        if tunnel:
            tframe = ACR122DirectTransmitCmd(data={"data_in": cmd.bytes()})
            response = self._connection.write(tframe, tunnel=True)
            response = ACR122DirectTransmitResp(bdata=response.child())
            return response
        else:
            response = self._connection.write(cmd)
            return response
