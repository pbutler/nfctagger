"""
Can be run from python -m nfctagger
This is mostly a test for reading and writing to a tag
"""
from datetime import datetime
from typing import Dict

import ndef
from loguru import logger
from smartcard.CardMonitoring import CardMonitor
from smartcard.CardMonitoring import CardObserver
from smartcard.util import toHexString

from .devices.ntag import NTag
from .devices.pcsc import PCSC
from .tlv import NDEF_TLV

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
        """
        The handler for the pyscard observer code.
        """
        (addedcards, _) = handlers
        for card in addedcards:
            logger.info(f"Card detected, ATR: {toHexString(card.atr)}")
            logger.info(f"Card ATR: {decode_atr(toHexString(card.atr))}")
            try:
                connection = card.createConnection()
                connection.connect()
                # use the connection to create the necesary objects
                sc = PCSC(connection)

                # drill down to get the tag object
                tag: NTag = sc.get_tag()

                logger.info(tag.get_tag_version())
                #For now this is a test statement to read the first 4 bytes of the user memory
                logger.info(tag.mem_read4(0))

                # read the entire user memory (higher level)
                data = tag.mem_read_user()

                # parse the data from NDEF TLV
                tlv = NDEF_TLV(bdata=data)
                logger.info(tlv)

                # get the V from the TLV and print it
                decoder = ndef.message_decoder(tlv._data.value)
                for record in decoder:
                    logger.info(record)

                # write a new record to the tag, overwriting the old
                rec = ndef.TextRecord(f"Hello, World!: {datetime.now()}")
                ndef_msg = b"".join(ndef.message_encoder([rec]))

                # build a valid TLV entry with the ndef message to be written
                data = NDEF_TLV(data={"value": ndef_msg})
                logger.info(data)
                tag.mem_write_user(data.bytes())

            except Exception as e:
                logger.exception(f"An error occurred: {e}")
                raise


def main():
    #nothing fancy here this is just how pyscard works, see observer above
    print("Starting NFC card processing...")
    cardmonitor = CardMonitor()
    cardobserver = PCSCObserver()
    cardmonitor.addObserver(cardobserver)

    try:
        input("Press Enter to stop...\n")
    finally:
        cardmonitor.deleteObserver(cardobserver)


if __name__ == "__main__":
    main()
