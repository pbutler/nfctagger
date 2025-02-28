from importlib.metadata import version

__author__ = "Patrick Butler"
__email__ = "pbutler@killertux.org"
__version__ = version("nfctagger")

from queue import Queue, Empty
import threading
from typing import Dict, Optional

from .devices.pcsc import PCSC

from loguru import logger
from smartcard.CardMonitoring import CardMonitor
from smartcard.CardMonitoring import CardObserver
from smartcard.util import toHexString

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
    """
    Observer class for NFC card detection and processing.
    Observes and runs a callback on any new cards detected.
    """
    def __init__(self, callback_fn=None):
        """
        :param callback_fn: Function to call when a card is detected,
        this funtion takes a single argument PCSC object.
        """
        super().__init__()
        self._fn = callback_fn
        logger.info("Starting NFC card processing...")
        self._cardmonitor = CardMonitor()
        self._cardmonitor.addObserver(self)

    def stop(self):
        self._cardmonitor.deleteObserver(self)
        logger.info("Stopped NFC card processing.")

    def update(self, observable, handlers):
        """
        The handler for the pyscard observer code.
        """
        (addedcards, _) = handlers
        for card in addedcards:
            logger.info(f"Card detected, ATR: {toHexString(card.atr)}")
            atr = decode_atr(toHexString(card.atr))
            logger.info(f"Card ATR: {atr}")
            if atr["Standard"] != "ISO 14443A, Part 3":
                logger.warning(f"Card standard not supported: {atr['Standard']}")
                continue
            try:
                connection = card.createConnection()
                connection.connect()
                if self._fn:
                    self._fn(connection)
            except Exception as e:
                logger.exception(f"An error occurred: {e}")
                raise

class PCSCWaiter(PCSCObserver):
    """
    Waiter, serves up PCSC objects to be processed as cards come in.
    This is done using a queue to safely pass data across threads.
    """
    def __init__(self):
        self._queue = Queue()
        super().__init__(self._handler)

    def _handler(self, connection):
        self._queue.put(connection)

    def get_next_connection(self, timeout=None) -> Optional[PCSC]:
        """
        Get the connection to the card or if none appears before timeout
        return None.

        :param timeout: how long to wait before failing and returning None
        """
        try:
            connection = self._queue.get(timeout=timeout)
            print(connection)
        except Empty:
            return None
        return PCSC(connection)
