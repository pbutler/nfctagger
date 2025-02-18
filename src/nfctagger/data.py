from typing import Optional, Union

from construct import (
    Container,
    GreedyBytes,
)
from construct.core import Construct


class Frame:
    def __init__(
        self,
        *,
        data: Optional[dict] = None,
        bdata: Optional[Union[bytes, bytearray]] = None,
    ):
        """
        A simple binary parsing and building class.  By default it
        grabs all bytes until the end of stream.  This can be subclassed
        to provide more specific parsing and building by overriding
        the _struct function to return an appropriate Construct object.

        Only one of data or bdata should be defined.

        :param data: if defined a dictionary describing the data to be
        represented in biary, defaults to None
        :type data: dict, optional
        :param bdata: the binary data which upon init will be parsed, defaults to None
        :type bdata: bytes or bytearray, optional
        """
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
        """
        Return the construct object that will be used to parse and build
        the binary data.

        :return: Construct object that can be used for parsing and building
        """
        return GreedyBytes  # pyright: ignore

    def bytes(self) -> bytes:
        """
        return the binary representation of the data

        :return: binary representation of the data
        """
        return self._parser.build(self._data)

    def __len__(self) -> int:
        """
        Length of the binary representation of the data

        :return: Length of the binary representation of the data
        """
        return len(self.bytes())

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}: {self._data}>"


class Response(Frame):
    """Response frame"""

    pass


class Command(Frame):
    """Command frame"""

    pass
