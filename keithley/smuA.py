##Modified for Keithley 2600B series which replaces SCPI with TSP protocol
from __future__ import division
from drivepy import visaconnection
from time import sleep

NPLC=1 # Default integration time
class smua(object):
    """ Class for the source measure unit which provides high level commands for setting and reading the current """
    def __init__(self,addr="GPIB0::26::INSTR",autoZero=True,disableScreen=False,defaultCurrent=10e-3, currRange=1e-3):
        self._smu=VisaConnection(addr, defaultCurrent)
        self._smu.write("smua.reset()")
#        self._smu.write(":FORM:ELEM:SENS VOLT,CURR")
        if disableScreen:
            self._smu.write("display.clear()")
        self.setCurrent(0)
        self.setBeepState(1)
        self.setOutputState(1)
        self.setBeepState(0)
        if not autoZero:
            self._smu.write("smua.measure.autozero = 0") # Turn off auto-zero to improve speed
        self._smu.write("smua.measure.nplc = "+str(NPLC))
        self.setSrcCurrRange(currRange)        
        
    def setCurrent(self,setCurr,Vcomp=3.5):
        """ Sets the current and returns a voltage from SMU"""
        # Set source mode
#        self._smu.write(":SOUR:FUNC CURR; :SOUR:CURR:MODE FIX")
        # Setup voltage measure function
        self._smu.write("smua.source.limitv = "+str(Vcomp))
        self._smu.write("smua.source.func = smua.OUTPUT_DCAMPS")
        # Set current and range. Would be nice to set the range automatically based on supplied current
        self._smu.write("smua.source.leveli = "+str(setCurr)) 
        

    def setSrcCurrRange(self,rangei):
        self._smu.write("smua.source.rangei = " + str(rangei))

    def setMeasCurrRange(self,rangei):
        self._smu.write("smua.measure.rangei = " + str(rangei))

    def setSrcVoltRange(self,rangev):
        self._smu.write("smua.source.rangev = " + str(rangev))

    def setMeasVoltRange(self,rangev):
        self._smu.write("smua.measure.rangev = " + str(rangev))
    
    def measure(self):
        """ Returns (voltage,current) measurement tuple from SMU """
        assert self.state, "The SMU needs to be turned ON to make an ouput measurement"
        readStr=self._smu.readQuery("print(smua.measure.iv())").split('\t')
        return (float(readStr[0]),float(readStr[1]))
    
    def autoZeroOnce(self):
        """ This is a workaround to autozero the SMU. ':SYS:AZER:STAT ONCE' would be better but not working. 
        This autoZero command should be called more than every 10 minutes """
        self._smu.write("smua.measure.nplc = "+str(2*NPLC))
        self._smu.write("smua.measure.nplc = "+str(NPLC))

    def setBeepState(self,state):
        """ Enable or disable the beeper """        
        if state=="ON" or state==1 or state==True:
            self._smu.write("beeper.enable = 1")
        elif state=="OFF" or state==0 or state==False:
            self._smu.write("beeper.enable = 0")
        else:
            raise TypeError,"Type error setting beeper state of SMU. Examples of correct state are ('ON','OFF',True,0)"       

    def setOutputState(self,state):
        """ Turns the SMU on or off depending on state. state can be ('ON'/True/1), ('OFF',False,0)"""
        if state=="ON" or state==1 or state==True:
            self._smu.write("smua.source.output = smua.OUTPUT_ON")
        elif state=="OFF" or state==0 or state==False:
            self._smu.write("smua.source.output = smua.OUTPUT_OFF")
        else:
            raise TypeError,"Type error setting state of SMU. Examples of correct state are ('ON','OFF',True,0)"
        # wait for the output to finish switching.
        sleep(10e-3)
        # set the state so we can keep track of it
        self.state=state

class VisaConnection(visaconnection.VisaConnection):
    """ Abstraction of the VISA connection for consistency between implementation of instrument classes """
    def __init__(self,addr,defaultCurrent):
        super(VisaConnection,self).__init__(addr)  
        self.defaultCurrent=defaultCurrent
    def __del__(self):
        self._smu.write("smua.source.output = smua.OUTPUT_OFF")
#        self.write(":SOUR:CURR:RANGE 100e-3;:SOUR:CURR:LEV "+str(self.defaultCurrent))
#        self.write("DISP:ENAB 1")
#        self.write(":SYST:LOC")        
