from __future__ import division
import ctypes,time,string,numpy
DLL_NAME="uart_library.dll"
BAUD_RATE=115200
READ_BUFFER_SIZE=256
NUM_POSITION=8
SEP_STRING="\r"

class FilterWheel(object):
    """Class to control the Thor Labs FW102C filter wheel position"""
    def __init__(self, *args, **kwargs):
        return super(FilterWheel, self).__init__(*args, **kwargs)
        self.connection=USBConnection()
        self.setPositionCount(NUM_POSITION)
        self.maxPosIndex=NUM_POSITION-1
        self.setSpeedMode(1)
        self.setSensorMode(0)

    def setPosition(self,position):
        """ Set position, where position is an integer starting from 0"""
        position=int(position)
        if position <0 or position > self.maxPosIndex:
            raise InvalidValueError, "The specified position was not valid. Please specify a value between 0 and 7"
        self.connection.write("pos="+position)
    def getPosition(self):
        """ Get position, where position is an integer starting from 0"""
        return int(self.connection.query("pos?"))
    def setPositionCount(self,posCount):
        """ Set position count: it can either be 6 or 12"""
        self.connection.write("pcount="+int(posCount))
    def getPositionCount(self):
        """ Get position count: it can either be 6 or 12"""
        return int(self.connection.query("pcount?"))
    def setTriggerMode(self,mode):
        """ Set external trigger mode to either input (0) or output (1) """
        self.connection.write("trig="+int(mode))
    def getTriggerMode(self):
        """ Get external trigger mode, with return value either input (0) or output (1) """
        int(self.connection.query("trig?"))
    def setSpeedMode(self,mode):
        """ Set speed mode to either slow (0) or fast (1) """
        self.connection.write("speed="+int(mode))
    def getSpeedMode(self):
        """ Get speed mode, with return value either slow (0) or fast (1) """
        int(self.connection.query("speed?"))
    def setSensorMode(self,mode):
        """ Set sensor mode to either: off when idle (0), or always on (1) """
        self.connection.write("sensors="+int(mode))
    def getSensorMode(self):
        """ Get sensor mode, with return value either: off when idle (0), or always on (1) """
        int(self.connection.query("sensors?"))
    def saveSettings(self):
        """ Save all settings to device non-volatile memory """
        self.connection.write("save")

class USBConnection(object):
    """ Abstraction of the low level connection to USB bus so that destructor can be used without circular
    references as per http://eli.thegreenplace.net/2009/06/12/safely-using-destructors-in-python/.
    This class is essentially a wrapper for the Thor Labs USB Driver library uart_library.dll"""
    def __init__(self,portNumber=None):
        """ Open the USB connection """
        self.readBufferSize=READ_BUFFER_SIZE
        try:
            self.lib=ctypes.WinDLL(DLL_NAME)
        except Exception,e:
            raise PowerMeterLibraryError,"Could not load the power meter library " + DLL_NAME + ". \n" + e.args[0]
        # If the port number was not specified then look for available ports
        if portNumber==None:
            # Get list of available devices
            readBuffer=ctypes.create_string_buffer(self.readBufferSize)
            s=self.lib.fnUART_LIBRARY_list(readBuffer,self.readBufferSize)
            ports=readBuffer.value.strip().split(",")
            portNumber=int(ports[0])
        # Open the usb device specified by portNumber
        s=self.lib.fnUART_LIBRARY_open(portNumber,BAUD_RATE)
        if s<0:
            raise CommError, "Connection to port=" + str(portNumber) + " could not be initialized and returned " + str(s)
    def __del__(self):
        """ Destructor method unitializes the USB connection """
        self.lib.fnUART_LIBRARY_close()
    def write(self,writeString):
        """ Writes a single command to the USB device"""
        s=self.lib.fnUART_LIBRARY_write(writeString+SEP_STRING, len(writeString+SEP_STRING))
        #s=self.lib.fnUART_LIBRARY_Set(writeString+SEP_STRING, len(writeString+SEP_STRING))
        if s<0:
            raise CommError, "Writing of command '" + writeString + "' was not succesful and returned " + str(s)
    
    def read(self):
        """ Reads the response from power meter """
        readBuffer=ctypes.create_string_buffer(self.readBufferSize)
        s=self.lib.fnUART_LIBRARY_read(readBuffer,self.readBufferSize)
        if s<0:
            raise CommError, "Reading from device was not succesful and returned " + str(s)
        return readBuffer.value

    def query(self,queryString):
        """ query the device with queryString and return the result """
        readBuffer=ctypes.create_string_buffer(self.readBufferSize)
        s=self.lib.fnUART_LIBRARY_Get(queryString+SEP_STRING,readBuffer)
        if s==0:
            return readBuffer.value
        elif s==0xEA:
            raise CommError, "The command "+queryString+" was not defined"
        elif s==0xEB or s==0xEC:
            raise CommError, "Timeout querying the device with command: "+queryString
        elif s==0xED:
            raise CommError, "Invalid string buffer error returned when querying with command: "+queryString
      
    def clearComQueue(self):
        """ Clears the communication queue in case communication was interrupted somehow. Probably not needed. """
        commStr=""
        while 1:
            try:
                commStr+=self.read()
            except CommError:
                break
        return commStr

class CommError(Exception): pass
class InvalidValueError(Exception): pass