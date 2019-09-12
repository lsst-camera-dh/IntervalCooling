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
	comp = getattr(refrig,target)().setSwitchOn(0,True)

def turnOff( compid ):
# Turn on Cold1/Cold2
	target="Cold{}".format(compid)
	print "turnOff %s" % target
	comp = getattr(refrig,target)().setSwitchOn(0,False)

def getPower( compid ):
	target="Cold{}".format(compid)
	val = float(getattr(refrig,target)().CompPower().getValue())
	print "%s = %f" % ( target, val )
	return val

def getTemp():
	tempref = [
#		"Cold_Temp/CLP-RTD-02",
		"Cold_Temp/CLP-RTD-03",
#		"Cold_Temp/CLP-RTD-52",
#		"Cold_Temp/CLP-RTD-53"
	]
	temparr = []
	for aref in tempref:
		temparr.append(float(getattr(thermal,aref)().getValue()))
	val = sum(temparr)/(len(temparr))
	print "Averaged temp = %f" % val
	return val

def Phase1( ):

	# 1. Start cold1 compressor.  Cold1 compressor will spin after 2 minutes delay.
	turnOn(1)
	print "Wait 110 sec"
	time.sleep(110)
	# check if a compressor consumes reasonably power
	while getPower(1)<1000:
		time.sleep(3)

	# 2. Set trim heater at 150 W with -Y set at diabled once cold1 compressor spins.
	thermal.enableColdSection(0, False)  # uncheck Enable -Y cold htrs
	thermal.enableColdSection(1, True)  # check Enable +Y cold htrs
	thermal.setTrimHeaterPower(0,150) # 0: -Y
	thermal.setTrimHeaterState(0, 1)  # running at fixed power

	# 3. Switch off cold1 compressor and trim heater after cold1 compressor has a run time of 2 minutes.
	time.sleep(120)
	thermal.setTrimHeaterState(0, 0)  # 
	turnOff(1)

	if getTemp()<-35:
		# exit this phase keeping the compressor system running.
		return False

	# 4. Eight (8) minutes later, start cold2 compressor.  Cold2 compressor will spin after 2 minutes delay.
	time.sleep(480)

	turnOn(2)
	print "Wait 110 sec"
	time.sleep(110)
	# check if a compressor consumes reasonably power
	while getPower(2)<1000:
		time.sleep(3)

	# 5. Set trim heater at 150 W with +Y set at diabled once cold2 compressor spins.
	thermal.enableColdSection(0, True)  # uncheck Enable -Y cold htrs
	thermal.enableColdSection(1, False)  # check Enable +Y cold htrs
	thermal.setTrimHeaterPower(0,150) # 0: -Y
	thermal.setTrimHeaterState(0, 1)  # running at fixed power

	# 6. Switch off cold2 compressor and trim heater after cold2 compressor has a run time of 2 minutes.
	time.sleep(120)
	thermal.setTrimHeaterState(0, 0)
	turnOff(2)

	if getTemp()<-35:
		# exit this phase keeping the compressor system running.
		return False

	# 7. Eight (8) minutes later, return to step 1.
	time.sleep(480)

	return True

def Phase2():
	# first turn on both compressor separately, giving a wait between two
	if getPower(1)<1000:
		turnOn(1)
		time.sleep(5)
	if getPower(2)<1000:
		turnOn(2)

	# set trim heater 
	thermal.setPlateTemperature(0, -40.0) # cold
#	thermal.setPlateTemperature(1, -40.0) # cryo
	# turn on trim heaters
	thermal.setTrimHeaterState(0, -1) # cold
#	thermal.setTrimHeaterState(1, -1) # cryo

	# set aux heater power
	thermal.setAuxHeaterPower(2,300) # center
	thermal.setAuxHeaterPower(0,0) # -Y
	thermal.setAuxHeaterPower(1,150) # +Y

	# turn on aux heaters
	thermal.setAuxHeaterState(0,1) # center
#	thermal.setAuxHeaterState(1,0) # -Y
	thermal.setAuxHeaterState(2,1) # +Y

if __name__ == "__main__":
	print "Phase1"
	while Phase1():
		print getTemp()

	print "Phase2"
	Phase2()

