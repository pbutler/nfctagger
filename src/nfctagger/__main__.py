"""
Can be run from python -m nfctagger
This is mostly a test for reading and writing to a tag
"""
import argparse
import sys
from datetime import datetime
from typing import Dict

from loguru import logger
from smartcard.CardMonitoring import CardMonitor
from smartcard.CardMonitoring import CardObserver
from smartcard.util import toHexString

import ndef
from . import __version__
from . import PCSCWaiter
from .devices.ntag import NTag
from .devices.pcsc import PCSC
from .ndef import NDEF
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


def handle(sc: PCSC):
    """
    Handle the NFC card connection and process the data.
    """
    # drill down to get the tag object
    tag: NTag = sc.get_tag()

    logger.info(tag.get_tag_version())
    #For now this is a test statement to read the first 4 bytes of the user memory
    logger.info(tag.mem_read4(0))

    # read the entire user memory (higher level)
    data = tag.mem_read_user()

    #TODO: Write code to parse ndefs at a higher level
    # parse the data from NDEF TLV
    tlv = NDEF_TLV(bdata=data)
    logger.info(tlv)

    # get the V from the TLV and print it
    decoder = ndef.message_decoder(tlv._data.value)
    for record in decoder:
        logger.info(record)


    # write a new record to the tag, overwriting the old
    ndefs = NDEF()
    ndefs.add_uri("https://pypi.org/project/nfctagger/")
    ndefs.add_text(f"Hello, World!: {datetime.now()}")

    # build a valid TLV entry with the ndef message to be written
    logger.info(ndefs)
    tag.mem_write_user(ndefs.bytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-q", "--quiet", action="store_false", dest="verbose",
                        help="don't print status messages to stdout")
    parser.add_argument("--version", action="version",
                        version="%(prog)s " + __version__)
    #parser.add_argument("args", type=str, nargs="*",
    #                    help="an integer for the accumulator")
    parser.add_argument("--cards", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=1)
    options = parser.parse_args()
    

    
    print("Starting NFC card processing...")
    wait = PCSCWaiter()

    ncards = 0
    while True:
        if options.cards > 0 and ncards >= options.cards:
            break
        # wait for a card to be detected for 1 second
        connection = wait.get_next_connection(timeout=1)
        if connection is None:
            continue
        ncards += 1
        handle(connection)
    return 0

if __name__ == "__main__":
    sys.exit(main())
