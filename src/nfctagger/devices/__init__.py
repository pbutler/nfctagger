from loguru import logger

from ..data import (
    Response,
    Command,
)


class Device:
    """Device writes to it's connection"""

    def __init__(self, connection):
        self._connection = connection
        pass

    def write(self, cmd: Command) -> Response:
        logger.debug(f">>> {cmd}")
        response = self._connection.write(cmd.bytes())
        logger.debug(f"<<< {response}")
        return response


class ParentDevice(Device):
    possible_children = []

    def __init__(self, connection):
        super().__init__(connection)
        self._child = self._identify_child()

    def _identify_child(self):
        for child in self.possible_children:
            if child.identify(self):
                return child(self)


class Tag(Device):
    pass
