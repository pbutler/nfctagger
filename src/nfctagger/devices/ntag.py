"""
Reference to the Protocol: https://www.nxp.com/docs/en/data-sheet/NTAG213_215_216.pdf
"""

from typing import Union

import construct as c
from loguru import logger

from . import Device
from . import Tag
from ..data import Command
from ..data import Response


class NTagResponse(Response):
    """Generic NTAG21x response"""

    pass


class NTagVersionCmd(Command):
    """
    This command is used to get the version of the ntag chip (size is
    inferrable from this), Command is a simple 0x60 byte
    """

    def __init__(self, *, data=None, bdata=None):
        super().__init__(data={}, bdata=bdata)

    def _struct(self):
        return c.Struct(
            "cmd" / c.Const(b"\x60"),
        )


class NTagReadCmd(Command):
    """Read Command"""

    def _struct(self):
        return c.Struct(
            "cmd" / c.Const(b"\x30"),
            "addr" / c.Int8ul,  # pyright: ignore
        )


class NTagReadResp(Response):
    """Read response, contains the data read"""

    def _struct(self) -> c.Construct:
        return c.Struct("data" / c.GreedyBytes)  # pyright: ignore


class NTagWriteCmd(Command):
    """Write command contains the address and datat to write"""

    def _struct(self):
        return c.Struct(
            "cmd" / c.Const(b"\xa2"),
            "addr" / c.Int8ul,  # pyright: ignore
            "data" / c.GreedyBytes,  # pyright: ignore
        )


class NTagWriteResp(Response):
    """Write response is simply an ack packet which we don't get to see"""

    def _struct(self) -> c.Construct:
        return c.Struct("ack" / c.GreedyBytes)  # pyright: ignore


class NTagVersionResp(Response):
    """
    Version response, contains identifying info which can figure out
    size
    """

    def _struct(self):
        return c.Struct(
            "header" / c.Bytes(1),
            "vendor" / c.Bytes(1),
            "prod_type" / c.Bytes(1),
            "prod_subtype" / c.Bytes(1),
            "major_ver" / c.Bytes(1),
            "minor_ver" / c.Bytes(1),
            "storage_size"
            / c.Enum(c.Bytes(1), ntag213=b"\x0f", ntag215=b"\x11", ntag216="b\x13"),
            "protocol_type" / c.Bytes(1),
        )

    def mem_size(self):
        assert self._data is not None
        return {
            "ntag213": 144,
            "ntag215": 504,
            "ntag216": 888,
        }[self._data.storage_size]


class NTag(Tag):
    """Implementation of the NTAG21x Tag"""

    def __init__(self, connection: Device):
        super().__init__(connection)
        # Default values for NTAG215
        self._size = 540
        self._user_size = 504
        # first user, non-config page is 4
        self._user_start_page = 4

    @classmethod
    def identify(cls, parent: Device) -> bool:
        # TODO Implement actual identification
        return True

    def write(self, cmd: Command, tunnel: bool = False) -> Response:
        """
        Write a command to the device

        :param cmd: Command to send to device
        :param tunnel: should always be False
        :return: Response from the device
        """

        # nothing to tunnel past here to
        assert not tunnel
        resp = self._connection.write(cmd, tunnel=True)
        return NTagResponse(bdata=resp.child())

    def get_tag_version(self):
        """
        Get the tag version (mostly the type to infer the size)
        """
        response = self.write(NTagVersionCmd())
        response = NTagVersionResp(bdata=response.bytes())
        self._user_size = response.mem_size()
        return self._user_size

    def mem_read4(self, address: int):
        """
        Read 4 pages of the memory from address

        :param address: address to read from (in pages)
        """

        response = self.write(NTagReadCmd(data={"addr": address}))
        response = NTagReadResp(bdata=response.bytes())
        return response._data.data

    def mem_read_user(self):
        """
        Read all user writeable memory for storage. i.e. not the config memory
        """
        ret = b""
        addr = self._user_start_page
        while len(ret) < self._user_size:
            data = self.mem_read4(addr)
            ret += data
            addr += 4
        return ret[: self._user_size]

    def mem_write4(self, address: int, data: Union[bytes, bytearray]):
        """
        Write 4 bytes of memory (1 page)

        :param address: address to write to by page #
        :param data: data, 4 bytes to write
        """
        assert len(data) == 4
        response = self.write(NTagWriteCmd(data={"addr": address, "data": data}))
        response = NTagWriteResp(bdata=response.bytes())

    def mem_write_user(self, data: Union[bytes, bytearray]):
        """
        Write data to the user memory starting at the first user page

        :param data: data to write
        """
        address = self._user_start_page
        assert len(data) <= self._user_size

        # Write in 4 byte chunks
        writes = len(data) // 4
        for i in range(writes):
            self.mem_write4(address + i, data[i * 4 : i * 4 + 4])
        leftover = len(data) % 4

        # if we send a non 4 byte chunk, read in the last block and
        # append the data with the missing bytes
        if leftover:
            rewrites = self.mem_read4(address + writes)[leftover:4]
            assert len(rewrites) <= 4
            last_blk = data[writes * 4 :] + rewrites
            assert 0 < len(last_blk) <= 4
            self.mem_write4(address + writes, last_blk)
