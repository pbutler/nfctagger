import pytest
from ndef import TextRecord
from nfctagger.ndef import NDEF


def test_ndef_parse_text():
    bdata = b"\x03\x0b\xd1\x01\x07T\x02entest\xfe"
    data = NDEF.parse(bdata)
    assert data is not None
    assert len(data.records) == 1
    record = data.records[0]
    assert isinstance(record, TextRecord)
    assert record.text == "test"
    assert record.language == "en"
    assert record.encoding == "UTF-8"


def test_ndef_parse_junk():
    with pytest.raises(Exception):
        bdata = b"\x04\x0b\xd1\x01\x07T\x02entest\xfe"
        data = NDEF.parse(bdata)

def test_ndef_parse_junk2():
    with pytest.raises(Exception):
        bdata = b"\x03\x0c\xd1\x01\x07T\x02entest\xfe"
        data = NDEF.parse(bdata)
