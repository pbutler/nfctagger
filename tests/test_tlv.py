from nfctagger.tlv import NDEF_TLV

def test_tlv_parse_small():
    """Type=0x03, length=0x01, value=0x01, footer=0xfe"""
    bdata = b"\x03\x01\x01\xfe"
    data = NDEF_TLV(bdata=bdata)
    assert data._data.length == 1
    assert data._data.value == b"\x01"

def test_tlv_parse_large():
    """Type=0x03, length=0x01, value=0x01, footer=0xfe"""
    bdata = b"\x03\xff\x01\x04" + (b"\x01" * 260) + b"\xfe"
    data = NDEF_TLV(bdata=bdata)
    assert data._data.length == 260
    assert data._data.value == bytes(bytearray(0x01 for _ in range(260)))

def test_tlv_build_small():
    short = NDEF_TLV(data={"value": bytearray(0x01 for _ in range(1))})
    bdata = b"\x03\x01\x01\xfe"
    assert short.bytes() == bdata

def test_tlv_build_large():
    long = NDEF_TLV(data={"value": bytearray(0x01 for _ in range(260))})
    bdata = b"\x03\xff\x01\x04" + (b"\x01" * 260) + b"\xfe"
    assert long.bytes() == bdata

# TODO: Test for missing terminal char
# TODO: Test for incorrect length > and < actual length
