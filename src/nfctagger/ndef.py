import ndef
from .tlv import NDEF_TLV
from ndef import TextRecord
from ndef import UriRecord

class NDEF:
    def __init__(self, records=None):
        if records is None:
            records = []
        self.records: list[ndef.Record] = records

    def __str__(self):
        return f"NDEF({self.records})"

    def add_uri(self, uri):
        self.records += [UriRecord(uri)]

    def add_text(self, text, language='en', encoding='UTF-8'):
        self.records += [TextRecord(text, language=language, encoding=encoding)]

    def bytes(self):
        ndefbytes = b''.join(ndef.message_encoder(self.records))  # pyright: ignore
        tlv = NDEF_TLV(data={"value": ndefbytes})
        return tlv.bytes()
