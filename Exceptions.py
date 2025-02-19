"""
Created on 14.09.2016

@author: Stefan Rossmann
"""


class ModbusException(Exception):
    """
    classdocs
    """

    def __init__(self, message):
        """ Exception to be thrown if Modbus Server returns error code "Function Code not executed (0x04)"
        Attributes:
            expression -- input expression in which the error occurred
            message -- explanation of the error
        """
        self.expression = message
        self.message = message

    def __str__(self):
        return self.message


class SerialPortNotOpenedException(ModbusException):
    """
    classdocs
    """

    def __init__(self, message):
        """ Exception to be thrown if serial port is not opened
        Attributes:
            expression -- input expression in which the error occurred
            message -- explanation of the error
        """

        self.message = message


class ConnectionException(ModbusException):
    """
    classdocs
    """

    def __init__(self, message):
        """ Exception to be thrown if Connection to Modbus device failed
        Attributes:
            expression -- input expression in which the error occurred
            message -- explanation of the error
        """
        self.message = message


class FunctionCodeNotSupportedException(ModbusException):
    """
    classdocs
    """

    def __init__(self, message):
        """ Exception to be thrown if Modbus Server returns error code "Function code not supported"
        Attributes:
            expression -- input expression in which the error occurred
            message -- explanation of the error
        """
        self.message = message


class QuantityInvalidException(ModbusException):
    """
    classdocs
    """

    def __init__(self, message):
        """ Exception to be thrown if Modbus Server returns error code "quantity invalid"
        Attributes:
            expression -- input expression in which the error occurred
            message -- explanation of the error
        """
        self.message = message


class StartingAddressInvalidException(ModbusException):
    """
    classdocs
    """

    def __init__(self, message):
        """ Exception to be thrown if Modbus Server returns error code "starting adddress and quantity invalid"
        Attributes:
            expression -- input expression in which the error occurred
            message -- explanation of the error
        """
        self.message = message


class CRCCheckFailedException(ModbusException):
    """
    classdocs
    """

    def __init__(self, message):
        """ Exception to be thrown if CRC Check failed
        Attributes:
            expression -- input expression in which the error occurred
            message -- explanation of the error
        """

        self.message = message


class RequestExecutionException(ModbusException):
    """
    classdocs
    """

    def __init__(self, message):
        """ Exception to be thrown if the Command could not be executed
        Attributes:
            expression -- input expression in which the error occurred
            message -- explanation of the error
        """

        self.message = message


class TimeoutError(ModbusException):
    """
    classdocs
    """

    def __init__(self, message):
        """ Exception to be thrown if Request Timed out
        Attributes:
            expression -- input expression in which the error occurred
            message -- explanation of the error
        """

        self.message = message
