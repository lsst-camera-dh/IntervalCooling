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
		"Cold_Temp/CLP-RTD-03",
		"Cold_Temp/CLP-RTD-05",
		"Cold_Temp/CLP-RTD-50",
		"Cold_Temp/CLP-RTD-55"
	]
	temparr = []
	for aref in tempref:
		temparr.append(float(getattr(thermal,aref)().getValue()))
	val = sum(temparr)/(len(temparr))
	print "Averaged temp = %f" % val
	return val

def onecycle( ):
	turnOn(1)
	time.sleep(5)
	turnOn(2)
	while getPower(1)<1100:
		time.sleep(3)
	time.sleep(5)
	while getPower(1)<1100:
		time.sleep(3)
	time.sleep(60)
	turnOff(1)
	time.sleep(5)
	turnOff(2)

if __name__ == "__main__":
	while getTemp()>-40:
		# onecycle( )
		time.sleep(3)


