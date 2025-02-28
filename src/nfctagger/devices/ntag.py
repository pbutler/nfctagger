"""
Reference to the Protocol: https://www.nxp.com/docs/en/data-sheet/NTAG213_215_216.pdf
"""
import hashlib
from binascii import hexlify
from typing import Optional
from typing import Union

import construct as c
from loguru import logger

from . import Device
from . import Tag
from ..data import Command
from ..data import Frame
from ..data import Response

class ConfigPages(Frame):
    def _struct(self) -> c.Construct:
        return c.Struct(
            "mirror" / c.BitStruct(
                    "mirror_uid" / c.Flag, #pyright: ignore
                    "mirror_cnt" / c.Flag, #pyright: ignore
                    "mirror_byte" / c.BitsInteger(2),
                    "rfui0" / c.Const(0, c.BitsInteger(1)),
                    "strong_mod" / c.Flag, #pyright: ignore
                    "rfui1" / c.Const(0, c.BitsInteger(2)),
                ),
            "rfui0" / c.Const(b"\x00", c.Bytes(1)),
            "mirror_page" / c.Int8ul, #pyright: ignore
            "auth0" / c.Int8ul, #pyright: ignore
            "access" / c.BitStruct(
                    "prot" / c.Flag, #pyright: ignore
                    "cfglck" / c.Flag, #pyright: ignore
                    "rfui0" / c.Const(0, c.BitsInteger(1)),
                    "nfc_cnt_en" / c.Flag, #pyright: ignore
                    "nfc_cnt_pwd_prot" / c.Flag, #pyright: ignore
                    "authlim" / c.BitsInteger(3),
                ),
            "rfui1" / c.Bytes(3),
            "pwd" / c.Bytes(4), 
            "pack" / c.Bytes(2),
            "rfui2" / c.Const(b"\x00\x00"),
        )


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


class NTagPwdAuthCmd(Command):
    """Authenticate Command"""

    def _struct(self):
        return c.Struct(
            "cmd" / c.Const(b"\x1b"),
            "pwd" / c.Bytes(4),
        )

class NTagPwdAuthResp(Response):
    """Authenticate Response"""

    def _struct(self):
        return c.Struct(
            "pack" / c.Bytes(2),
        )

def get_pwd_pack(password: str, uid: bytes) -> tuple[bytes, bytes]:
    key = hashlib.scrypt(password.encode("utf-8"), salt=uid, n=2**14, r=8, p=1, dklen=6)
    return (key[:4], key[-2:])

class NTag(Tag):
    """Implementation of the NTAG21x Tag"""

    def __init__(self, connection: Device, tag_type: str = "ntag215"):
        super().__init__(connection)
        # Default values for NTAG215
        # first user, non-config page is 4
        self._user_start_page = 4
        self._confs = {
            "ntag213": {
                "size": 144,
                "user_size": 132,
            },
            "ntag215": {
                "size": 540, 
                "user_size": 504,
            },
            "ntag216": {
                "size": 924,
                "user_size": 888,
            },
        }
        self.set_type(tag_type)

    def set_type(self, tag_type: str):
        """
        Set the tag type to a different type than the default

        :param tag_type: type of tag, ntag213, ntag215, ntag216
        """
        self.type = tag_type
        self._size = self._confs[tag_type]["size"]
        self._user_size = self._confs[tag_type]["user_size"]
        self._page_len = self._size // 4

    @classmethod
    def identify(cls, parent: Device) -> bool:
        tmp = cls(parent)
        try: 
            tag_type = tmp.get_tag_version(config=True)
            logger.debug(f"NTag Identified tag as {tag_type}")
        except Exception:
            return False
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

    def get_uid(self) -> bytes:
        """
        Get the UID of the tag, will be a 7 byte value starting with 0x04
        """
        data = self.mem_read4(0)
        uid = data[:3] + data[4:8]
        bcc0 = data[3]
        bcc1 = data[8]
        assert uid[0] == 0x04
        assert bcc0 == (0x88 ^ uid[0] ^ uid[1] ^ uid[2])
        assert bcc1 == (uid[3] ^ uid[4] ^ uid[5] ^ uid[6])
        return uid

    def set_password(self, password: str):
        """
        Set the password for the tag, this will also set the pack

        :param password: password to set, will use an scrypt key
        derivation algorithm to create the PWD key and the PACK value
        """
        """
        Set the password for the tag
        """
        logger.debug("Setting password")
        uid = self.get_uid()
        pwd, pack = get_pwd_pack(password, uid)
        self.mem_write4(self._page_len - 2, pwd)
        self.mem_write4(self._page_len - 1, pack + b"\x00\x00")

    def authenticate(self, password: str):
        """
        Authenticate reader to the card.  Also verifies the pack value
        matches with what we expect.  There doesn't seem to be a 
        standard so this will only work with nfctagger.

        :param password: password to use for authentication
        """
        uid = self.get_uid()
        pwd, pack = get_pwd_pack(password, uid)
        response = self.write(NTagPwdAuthCmd(data={"pwd": pwd}))

        # NAK's look like blank responses
        if len(response.bytes()) != 2:
            logger.warning("Bad password")
            return False
        else:
            response = NTagPwdAuthResp(bdata=response.bytes())
            # if pack's don't match then this is either trying to fool 
            # us or is the wrong tag
            if response._data.pack == pack:
                return True
            else:
                logger.warning("Pack mismatch")
                return False

    def secure_page_after(self, page: int, readprot: Optional[bool] = None):
        """
        Secure the page after the given page

        :param page: page to start protecting
        :param readprot: True: protect pages from reading/writing
                         False: protect pages only from writing, 
                         None: Leave as is, don't change, defaults to None
        """
        logger.debug(f"Securing page {page} and up")
        bdata = self.mem_read4(self._page_len - 4)
        cpages = ConfigPages(bdata=bdata)
        logger.debug(f"Current Config: {cpages}")
        cpages._data.auth0 = page
        if readprot is not None:
            cpages._data.access.prot = readprot

        logger.debug(f"New Config: {cpages}")

        newdata = cpages.bytes()
        for i in range(2):
            self.mem_write4(self._page_len - 4 + i, newdata[i * 4: (i + 1) * 4])

    def get_cc(self):
        """
        Get the capability container
        """
        data = self.mem_read4(3)[:4]
        return data

    def get_tag_version(self, config: bool=False) -> str:
        """
        Get the tag version (mostly the type to infer the size)
        :param config: if true configure type based upon response
        otherwise just report back
        """
        response = self.write(NTagVersionCmd())
        response = NTagVersionResp(bdata=response.bytes())
        tag_type = response._data.storage_size
        if config:
            self.set_type(tag_type)
        return tag_type

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
        if len(data) != 4:
            raise ValueError("Data must be 4 bytes long")
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
