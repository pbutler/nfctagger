from loguru import logger
import construct as c

from . import Device, Tag
from ..data import Command
from ..data import Response


class NTagResponse(Response):
    pass


class NTagVersionCmd(Command):
    def __init__(self, *, data=None, bdata=None):
        super().__init__(data={}, bdata=bdata)

    def _struct(self):
        return c.Struct(
            "cmd" / c.Const(b"\x60"),
        )


class NTagReadCmd(Command):
    def _struct(self):
        return c.Struct(
            "cmd" / c.Const(b"\x30"),
            "addr" / c.Int8ul,  # pyright: ignore
        )


class NTagReadResp(Response):
    def _struct(self) -> c.Construct:
        return c.Struct("data" / c.GreedyBytes)  # pyright: ignore


class NTagWriteCmd(Command):
    def _struct(self):
        return c.Struct(
            "cmd" / c.Const(b"\xa2"),
            "addr" / c.Int8ul,  # pyright: ignore
            "data" / c.GreedyBytes,  # pyright: ignore
        )


class NTagWriteResp(Response):
    def _struct(self) -> c.Construct:
        return c.Struct("ack" / c.GreedyBytes)  # pyright: ignore


class NTagVersionResp(Response):
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
    def __init__(self, connection: Device):
        super().__init__(connection)
        self._size = 540
        self._user_size = 504
        self._user_start_page = 4

    @classmethod
    def identify(cls, connection: Device) -> bool:
        # TODO Implement
        return True

    def write(self, cmd: Command, tunnel=False) -> Response:
        assert not tunnel
        resp = self._connection.write(cmd, tunnel=True)
        return NTagResponse(bdata=resp.child())

    def get_tag_version(self):
        response = self.write(NTagVersionCmd())
        response = NTagVersionResp(bdata=response.bytes())
        self._user_size = response.mem_size()
        return self._user_size

    def mem_read4(self, address):
        response = self.write(NTagReadCmd(data={"addr": address}))
        response = NTagReadResp(bdata=response.bytes())
        return response._data.data
        print(response)

    def mem_read_user(self):
        ret = b""
        addr = self._user_start_page
        while len(ret) < self._user_size:
            data = self.mem_read4(addr)
            print(len(data), data)
            ret += data
            addr += 4
        return ret[: self._user_size]

    def mem_write4(self, address, data):
        response = self.write(NTagWriteCmd(data={"addr": address, "data": data}))
        response = NTagWriteResp(bdata=response.bytes())
        logger.debug(f"<{len(response)}")

    def mem_write_user(self, address, data):
        address = self._user_start_page + address
        assert len(data) <= self._user_size
        writes = len(data) // 4
        for i in range(writes):
            self.mem_write4(address + i, data[i * 4 : i * 4 + 4])
        leftover = len(data) % 4
        if leftover:
            rewrites = self.mem_read4(address + writes)[leftover:4]
            assert len(rewrites) <= 4
            last_blk = data[writes * 4 :] + rewrites
            assert 0 < len(last_blk) <= 4
            self.mem_write4(address + writes, last_blk)
