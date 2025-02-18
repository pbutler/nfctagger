from construct import GreedyBytes
from construct import Struct

from . import ParentDevice
from . import Tag
from ..data import Command
from ..data import Response
from .acr122 import ACR122U


class PCSCResp(Response):
    """Generic PCSC response"""
    def _struct(self):
        return Struct(
            "data_out" / GreedyBytes,  # pyright: ignore
        )

    def child(self):
        return self._data.data_out


class PCSC(ParentDevice):
    """ 
    This device is really an adapter for PCSC/PySCard.  As of now it 
    only send tunnel commands to actual devices
    """

    possible_children = [ACR122U,]

    def __init__(self, connection):
        super().__init__(connection)

    def write(self, cmd: Command, tunnel=False) -> Response:
        """
        Send command to device, right now ignores the tunnel flag

        :param cmd: command to send
        :param tunnel: if true, send command to child device, defaults to False
        :return: Rresponse received from device
        """

        response, sw1, sw2 = self._connection.transmit(list(cmd.bytes()))
        # check if response is okay 
        assert sw1 == 0x90 and sw2 == 0x00, "Response not okay"
        return PCSCResp(bdata=bytearray(response))

    def get_tag(self) -> Tag:
        """Grab the lowest level device and make sure it's a tag"""
        #TODO: Make this recusrsive through parent class
        cur = self
        while hasattr(cur, "_child"):
            cur = cur._child
            assert cur is not None
        assert isinstance(cur, Tag)
        return cur
