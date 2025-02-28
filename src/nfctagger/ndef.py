from typing import Optional
from typing import Union

import ndef
from .tlv import NDEF_TLV
from ndef import TextRecord
from ndef import UriRecord

class NDEF:
    def __init__(self, records: Optional[list[ndef.Record]] = None):
        """
        Creates an NDEF object to read/write NDEF records

        :param records: a list of NDEF records which will be parsed 
        into the final data
        """
        if records is None:
            records = []
        self.records: list[ndef.Record] = records

    @classmethod
    def parse(cls, bdata: Union[bytes, bytearray]) -> Optional['NDEF']:
        """
        parse a series of bytes into an NDEF object with a set of records

        :param bdata: bytes to be parsed
        """
        tlv = NDEF_TLV(bdata=bdata)
        records = ndef.message_decoder(tlv._data.value)
        if records is not None:
            return cls([r for r in records])
        else:
            return None

    def __str__(self):
        return f"NDEF({self.records})"

    def add_uri(self, uri: str):
        """
        create and add a simple URI record to the ndef message

        :param uri: uri to be added to the ndef message
        """
        self.records += [UriRecord(uri)]

    def add_text(self, text: str, language: str = 'en', encoding: str = 'UTF-8'):
        """
        add a text record to the message

        :param text: text to be added
        :param language: language text is to be in, defaults to 'en'
        :param encoding: encoding of bytes in text, defaults to 'UTF-8'
        """
        self.records += [TextRecord(text, language=language, encoding=encoding)]

    def bytes(self):
        """
        Generate a byte representation of the NDEF message
        """
        ndefbytes = b''.join(ndef.message_encoder(self.records))  # pyright: ignore
        tlv = NDEF_TLV(data={"value": ndefbytes})
        return tlv.bytes()
