from typing import Dict
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.util import toHexString
from smartcard.CardConnection import CardConnection

import ndef
from .tlv import NDEF_TLV
from .devices.pcsc import PCSC
from .devices.ntag import NTag
from datetime import datetime


def decode_atr(atr: str) -> Dict[str, str]:
    """Decode the ATR (Answer to Reset) string into readable components.
       Implementation from: https://rpi4cluster.com/python-nfc-writer-reader/

    Args:
        atr (str): ATR string.

    Returns:
        Dict[str, str]: Dictionary containing readable information about the card.
    """
    atr = atr.split(" ")

    rid = atr[7:12]
    standard = atr[12]
    card_name = atr[13:15]

    card_names = {
        "00 01": "MIFARE Classic 1K",
        "00 38": "MIFARE Plus® SL2 2K",
        "00 02": "MIFARE Classic 4K",
        "00 39": "MIFARE Plus® SL2 4K",
        "00 03": "MIFARE Ultralight®",
        "00 30": "Topaz and Jewel",
        "00 26": "MIFARE Mini®",
        "00 3B": "FeliCa",
        "00 3A": "MIFARE Ultralight® C",
        "FF 28": "JCOP 30",
        "00 36": "MIFARE Plus® SL1 2K",
        "FF[SAK]": "undefined tags",
        "00 37": "MIFARE Plus® SL1 4K",
        "00 07": "SRIX",
    }

    standards = {"03": "ISO 14443A, Part 3", "11": "FeliCa"}

    return {
        "RID": " ".join(rid),
        "Standard": standards.get(standard, "Unknown"),
        "Card Name": card_names.get(" ".join(card_name), "Unknown"),
    }


class PCSCObserver(CardObserver):
    """Observer class for NFC card detection and processing."""

    def update(self, observable, handlers):
        (addedcards, _) = handlers
        for card in addedcards:
            print(f"Card detected, ATR: {toHexString(card.atr)}")
            print(f"Card ATR: {decode_atr(toHexString(card.atr))}")
            try:
                connection = card.createConnection()
                connection.connect()
                sc = PCSC(connection)
                tag: NTag = sc.get_tag()
                print(tag)
                print(tag.get_tag_version())
                print(tag.mem_read4(0))
                data = tag.mem_read_user()
                tlv = NDEF_TLV().parse(data)
                assert tlv is not None
                print(tlv)
                decoder = ndef.message_decoder(tlv.value)
                for record in decoder:
                    print(record)

                rec = ndef.TextRecord(f"Hello, World!: {datetime.now()}")
                ndef_msg = b"".join(ndef.message_encoder([rec]))

                data = NDEF_TLV().build({"value": ndef_msg})
                print(data)
                tag.mem_write_user(0, data)

            except Exception as e:
                print(f"An error occurred: {e}")
                raise


def main():
    print("Starting NFC card processing...")
    cardmonitor = CardMonitor()
    cardobserver = PCSCObserver()
    cardmonitor.addObserver(cardobserver)

    try:
        input("Press Enter to stop...\n")
    finally:
        cardmonitor.deleteObserver(cardobserver)
        print(f"Stopped NFC card processing. Total cards processed: {cards_processed}")


if __name__ == "__main__":
    main()
