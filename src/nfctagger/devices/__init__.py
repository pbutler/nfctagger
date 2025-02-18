from loguru import logger

from ..data import Command
from ..data import Response


class Device:
    """
    Device object writes to it's connection, doesnt expect any 
    children that can be tunneled through to
    """

    def __init__(self, connection):
        """
        An init method for the Device class

        :param connection: For most devices this is whatever you can 
        write to talk to it.  We expect a write to return a bytes object
        that can then be casted to a  type of Response object
        """
        
        self._connection = connection
        pass

    @classmethod
    def identify(cls, parent: 'Device') -> bool:
        """
        A method to identify the device

        :param parent: The parent device that is trying to identify this 
        device
        :return: True if the device is identified, False otherwise
        """
        return False

    def write(self, cmd: Command) -> Response:
        logger.debug(f">>> {cmd}")
        response = self._connection.write(cmd.bytes())
        response = Response(bdata=response)
        logger.debug(f"<<< {response}")
        return response


class ParentDevice(Device):
    """
    Devices that have children that can be tunneled through to.  On 
    initialization, the device will identify the child and create an 
    instance of it and point to it.

    Attributes:
        possible_children (list[Device]):  a list of possible children
        types to check for
    """
    possible_children: list[type[Device]] = []

    def __init__(self, connection):
        """
        Does normal device init and then identifies the child

        :param connection: For most devices this is whatever you can 
        write to talk to it.  We expect a write to return a bytes object
        that can then be casted to a  type of Response object
        """
        super().__init__(connection)
        self._child = self._identify_child()

    def _identify_child(self):
        """
        Function that uses the possible_children list to identify the
        actual child device
        """
        for child in self.possible_children:
            if child.identify(self):
                return child(self)


class Tag(Device):
    pass
