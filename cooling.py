#!/usr/bin/env ccs-script
import sys
sys.path.insert(0,"/gpfs/slac/lsst/fs1/g/data/youtsumi/fp-scripts/lib")
from org.lsst.ccs.scripting import CCS, ScriptingTimeoutException
from org.lsst.ccs.bus.states import AlertState
from org.lsst.ccs.messaging import CommandRejectedException
from java.time import Duration
from java.lang import RuntimeException
from ccs import proxies
import re
import math
import time
import argparse
import logging

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def CCSattachProxy(target):
        """ Improve reliability """
        for i in range(3):
                logging.info( "{}: {}".format(target, i))
                try:
                        return CCS.attachProxy(target)
                except RuntimeException as ex:
                        logging.error( ex)
                        time.sleep(1)
                        pass
        raise

thermal = CCSattachProxy("thermal")
refrig = CCSattachProxy("refrig")

def turnOn( compid ):
# Turn on Cold1/Cold2
	target="Cold{}".format(compid)
	print "turnOn %s" % target
#	comp = getattr(refrig,target)().setSwitchOn(0,True)

def turnOff( compid ):
# Turn on Cold1/Cold2
	target="Cold{}".format(compid)
	print "turnOff %s" % target
#	comp = getattr(refrig,target)().setSwitchOff(0,False)

def getPower( compid ):
	target="Cold{}".format(compid)
	val = float(getattr(refrig,target)().CompPower().getValue())
	print "%s = %f" % ( target, val )
	return val

def getTemp():
	tempref = [
		"Cold_Temp/CLP-RTD-02",
		"Cold_Temp/CLP-RTD-03",
		"Cold_Temp/CLP-RTD-52",
		"Cold_Temp/CLP-RTD-53"
	]
	temparr = []
	for aref in tempref:
		temparr.append(float(getattr(thermal,aref)().getValue()))
	val = sum(temparr)/(len(temparr))
	print "Averaged temp = %f" % val
	return val

def Phase1( ):
	# first turn on both compressor separately, giving a wait between two
	turnOn(1)
	time.sleep(5)
	turnOn(2)
	# wait about 2 min to get them turned on
	time.sleep(110)
	# check if a compressor consumes reasonably power
	while getPower(1)<1100:
		time.sleep(3)
	time.sleep(5)
	# check another compressor
	while getPower(2)<1100:
		time.sleep(3)
	# run compressors for 1 min, then turn themm off
	time.sleep(60)

	if getTemp()<-35:
		# exit this phase keeping the compressor system running.
		return False

	turnOff(1)
	time.sleep(5)
	turnOff(2)
	# wait for 10 min
	time.sleep(600)

	return True

def Phase2():
	# set trim heater setpoint at -40C
	thermal.setPlateTemperature(0, -40.0)
	thermal.setPlateTemperature(1, -40.0)
	thermal.setPlateTemperature(2, -40.0)

	# turn on trim heaters
	thermal.setTrimHeaterState(0, 1)
	thermal.setTrimHeaterState(1, 1)
	thermal.setTrimHeaterState(2, 1)

	# turn on aux heaters
	thermal.setAuxHeaterPower(2,300)
	thermal.setAuxHeaterPower(0,150)
	thermal.setAuxHeaterPower(1,150)

if __name__ == "__main__":
	while Phase1():
		time.sleep(3)
	
	Phase2()




