#!/usr/bin/python3
#
# powercontroller2.py
#
# Control script for Allen Pomeroy PowerController hardware v2.4
# See pomeroy.us/2022/12/building-an-irrigation-power-controller/
# MCP23017 based I2C bus expansion board
# - 5x 24VAC valve relays
# - 2x 12VDC pump relay feeds
# - 3x 5v GPIO digital lines
# - AC Hz sensor
# 
# Turns pump and valve relays on or off.  No sample interrupt handling to measure frequency yet.
#

# WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING 
# It is recommended to only activate a maximum of two (2) valves and
# either or both pumps simultaneously to limit the aggregate current draw.
# Activating more valves simulaneously is likely to cause excessive heat
# generation and possible permanent damage to the circuit board or
# components.

# Copyright 2023 Allen Pomeroy - MIT license
#
# v1.3
# - updated pinout mapping for hardware v2.4 relays and pumps
# - IMPORTANT cannot use earlier versions since GPIO pinouts completely changed in hardware v2.4
# - pre-release code .. it's ugly and incomplete with little to no error checking
# v1.2
# - added command line argument processing
# - added syslog output for auditing/monitoring
# v1.1
# - add read of pin value prior to set
# v1.0
# - initial release
# - Uses Adafruit libraries
#   https://docs.circuitpython.org/projects/mcp230xx/en/latest/api.html#adafruit_mcp230xx.digital_inout.DigitalInOut.value
# - need to install the libraries prior to using this script
#   sudo pip3 install adafruit-circuitpython-mcp230xx
#
# TODO:
# - convert linear code to functions
# - add optional pin configuration to accomodate prototyping
#

# PowerController i2c bus address jumpers
#  A2 A1 A0
#  0  0  0  0x20
#  0  0  1  0x21
#  0  1  0  0x22
#  0  1  1  0x23
#  1  0  0  0x24
#  1  0  1  0x25 
#  1  1  0  0x26
#  1  1  1  0x27 (default)
#
# Hardware I/O configuration
#
# GPIO Pin Layout - PCB and Breadboard - HW v2.4
#
# GPIO-ID  PIN  IC-PIN  HW      BREADBOARD
# GPIOA0   0    21      -       RED
# GPIOA1   1    22      -       YEL
# GPIOA2   2    23      -       GREEN
# GPIOA3   3    24      ACSENSE BLUE
# GPIOA4   4    25      -       -
# GPIOA5   5    26      PUMP1   -
# GPIOA6   6    27      VALVE2  -
# GPIOA7   7    28      VALVE4  -
# GPIOB0   8     1      VALVE5  RELAY
# GPIOB1   9     2      VALVE3  -
# GPIOB2   10    3      VALVE1  -
# GPIOB3   11    4      PUMP2   -
# GPIOB4   12    5      -       -
# GPIOB5   13    6      LINE0   -
# GPIOB6   14    7      LINE1   - 
# GPIOB7   15    8      LINE2   -
#
# GPIO_INTA acsense
#
# example uses for external inputs
# line0 - water pressure sensor
# line1 - water flow sensor
# line2 - extra digital input
#
# Usage:
# powercontroller2.py {relay-name|all} {on|off}
# valve1, valve2, valve3, valve4, valve5, pump1, pump2, test
# 
# Optionally can specify "all" for relay name for "off" action.
# Can specify "test" "on" to run a loop through each relay activated
# sequentially TESTCOUNT times.
#
# WARNING WARNING WARNING WARNING WARNING WARNING WARNING WARNING 
# It is recommended to only activate a maximum of two (2) valves and
# either or both pumps simultaneously to limit the aggregate current draw.
# Activating more valves simulaneously is likely to cause excessive heat
# generation and possible permanent damage to the circuit board or
# components.

# -------
# imports
import board
import busio
import time
import configparser
import argparse
import syslog
from array import array
import sys
from digitalio import Direction
from adafruit_mcp230xx.mcp23017 import MCP23017

# ---------
# constants

version = "1.3"

# PCB
VALVE1PIN = 10
VALVE2PIN = 6
VALVE3PIN = 9
VALVE4PIN = 7
VALVE5PIN = 8
PUMP1PIN  = 5
PUMP2PIN  = 11
LINE0     = 13
LINE1     = 14
LINE2     = 15
ACSENSE   = 3

# array index
VALVE1 = 0
VALVE2 = 1
VALVE3 = 2
VALVE4 = 3
VALVE5 = 4
PUMP1  = 5
PUMP2  = 6
LINE0  = 7
LINE1  = 8
LINE2  = 9


# -------------
# configuration via command line parameters
#
# default constants defined in command line argument processing
# I2CADDR = 0x24 # A2=1, A1=0, A0=0
# TESTCOUNT = 3
# TESTONTIME = 1
# TESTOFFTIME = 0.1

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--i2caddress", 
                    help="I2C address of the PowerController board", action="store", type=str, default='0x27')
parser.add_argument("-t", "--testcount", 
                    help="Number of test cycles", type=int, action="store", default='3')
parser.add_argument("-o", "--testontime", 
                    help="On time for tests (sec)", type=float, action="store", default='1')
parser.add_argument("-s", "--syslog", 
                    help="Send syslog status messages", action="store_true")
parser.add_argument("-f", "--testofftime", 
                    help="Off time for tests (sec)", type=float, action="store", default='0.1')
parser.add_argument("-v", "--verbose", 
                    help="Print progress messages", action="store_true")
parser.add_argument("-r", "--relay", type=str, action="store", required=True,
                    choices=['valve1', 'valve2', 'valve3', 'valve4', 'valve5', 'pump1', 'pump2', 'test', 'all'],
                    help="Name of relay to operate on")
parser.add_argument("-a", "--action", type=str, action="store", required=True,
                    choices=['on', 'off'],
                    help="Action to perform on relay. Note relay 'all' can only accept action 'off'")

# parse the arguments
args         = parser.parse_args()
verbose      = args.verbose
testcount    = args.testcount
testontime   = args.testontime
testofftime  = args.testofftime
sendsyslog   = args.syslog
i2caddr      = int(args.i2caddress, 16)
relay        = args.relay
action       = args.action

if verbose == True:
  strHex = "0x%0.2X" % i2caddr
  print("startup .. version " + str(version))
  print("testcount " + str(testcount))
  print("testontime " + str(testontime))
  print("testofftime " + str(testofftime))
  print("address " + strHex)
  print("verbose " + str(verbose))
  print("sendsyslog " + str(sendsyslog))
  print("relay " + str(relay))
  print("action " + str(action))

if sendsyslog == True:
  syslog.syslog("startup .. version " + str(version))

# --------------
# error handlers

# usage error
def usageError(errno):
  print("usage: powercontroller2.py {relay-name|all} {on|off} error code " + str(errno))
  print("relay-name can be \"all\" for \"off\" action only")
  print("valve1  valve2  valve3  valve4  valve5  pump1  pump2  test")
  exit(1)

# error exit
def initError(errno):
  print("powercontroller2.py initialization error code " + str(errno))
  exit(errno)

# -----
# setup i2c handle and access

if sendsyslog == True:
  strHex = "0x%0.2X" % i2caddr
  syslog.syslog("initializing I2C at " + strHex)
  #syslog.syslog(syslog.LOG_INFO, "Test message at INFO priority")

try:
  i2c = busio.I2C(board.SCL, board.SDA)
except ValueError:
  if sendsyslog == True:
    syslog.syslog(syslog.LOG_WARNING, "initialization of I2C failed")
  initError(301)

# create MCP access
try:
  mcp = MCP23017(i2c,address=i2caddr)
except ValueError:
  if sendsyslog == True:
    syslog.syslog(syslog.LOG_WARNING, "initialization of MCP failed")
  initError(302)

# build list of all used output pins
relayPins = []
relayPins.append(mcp.get_pin(VALVE1PIN))
relayPins.append(mcp.get_pin(VALVE2PIN))
relayPins.append(mcp.get_pin(VALVE3PIN))
relayPins.append(mcp.get_pin(VALVE4PIN))
relayPins.append(mcp.get_pin(VALVE5PIN))
relayPins.append(mcp.get_pin(PUMP1PIN))
relayPins.append(mcp.get_pin(PUMP2PIN))

#relayPins.append(mcp.get_pin(int(config['HWv2']['VALVE1'])))

# set all the valve and pump pins to output
for pin in relayPins:
    pin.direction = Direction.OUTPUT
    # do not initialize all output pins to off
    # otherwise any relay that is currently on
    # will be forced off - only allowing one relay to
    # be on at a time.
    #pin.value     = False

# set all the port B line pins to input, with pullups
#for pin in port_b_pins:
#    pin.direction = Direction.INPUT
#    pin.pull = Pull.UP

#pin0.value = True  # GPIO0 / GPIOA0 to high logic level
#pin0.value = False # GPIO0 / GPIOA0 to low logic level


# must be three arguments
#if len(sys.argv) != 3  or (sys.argv[2] != "on" and sys.argv[2] != "off"):
#  usageError(201)

# capture relay and action from command line arguments
#relay  = sys.argv[1]
#action = sys.argv[2]

# check arguments
if relay == "all":
  if action == "off":
    if sendsyslog == True:
      syslog.syslog("executing all off")
    relayPins[VALVE1].value = False
    relayPins[VALVE2].value = False
    relayPins[VALVE3].value = False
    relayPins[VALVE4].value = False
    relayPins[VALVE5].value = False
    relayPins[PUMP1].value  = False
    relayPins[PUMP2].value  = False
  else:
    usageError(202)

elif relay == "valve1":
  if action == "on":
    if relayPins[VALVE1].value == True:
      if verbose == True:
        print("valve1 already on")
    else:
      if verbose == True:
        print("executing " + relay + " " + action)
      if sendsyslog == True:
        syslog.syslog("executing " + relay + " " + action)
      relayPins[VALVE1].value = True
    #print("current value of valve1 = {0}".format(relayPins[VALVE1].value))
  elif action == "off":
    if relayPins[VALVE1].value == False:
      if verbose == True:
        print("valve1 already off")
    else:
      if verbose == True:
        print("executing " + relay + " " + action)
      if sendsyslog == True:
        syslog.syslog("executing " + relay + " " + action)
      relayPins[VALVE1].value = False
  else:
    usageError(203)

elif relay == "valve2":
  if action == "on":
    if relayPins[VALVE2].value == True:
      if verbose == True:
        print("valve2 already on")
    else:
      if verbose == True:
        print("executing " + relay + " " + action)
      if sendsyslog == True:
        syslog.syslog("executing " + relay + " " + action)
      relayPins[VALVE2].value = True
  elif action == "off":
    if relayPins[VALVE2].value == False:
      if verbose == True:
        print("valve2 already off")
    else:
      if verbose == True:
        print("executing " + relay + " " + action)
      if sendsyslog == True:
        syslog.syslog("executing " + relay + " " + action)
      relayPins[VALVE2].value = False
  else:
    usageError(204)

elif relay == "valve3":
  if action == "on":
    if relayPins[VALVE3].value == True:
      if verbose == True:
        print("valve3 already on")
    else:
      if verbose == True:
        print("executing " + relay + " " + action)
      if sendsyslog == True:
        syslog.syslog("executing " + relay + " " + action)
      relayPins[VALVE3].value = True
  elif action == "off":
    if relayPins[VALVE3].value == False:
      if verbose == True:
        print("valve3 already off")
    else:
      if verbose == True:
        print("executing " + relay + " " + action)
      if sendsyslog == True:
        syslog.syslog("executing " + relay + " " + action)
      relayPins[VALVE3].value = False
  else:
    usageError(205)

elif relay == "valve4":
  if action == "on":
    if relayPins[VALVE4].value == True:
      if verbose == True:
        print("valve4 already on")
    else:
      if verbose == True:
        print("executing " + relay + " " + action)
      if sendsyslog == True:
        syslog.syslog("executing " + relay + " " + action)
      relayPins[VALVE4].value = True
  elif action == "off":
    if relayPins[VALVE4].value == False:
      if verbose == True:
        print("valve4 already off")
    else:
      if verbose == True:
        print("executing " + relay + " " + action)
      if sendsyslog == True:
        syslog.syslog("executing " + relay + " " + action)
      relayPins[VALVE4].value = False
  else:
    usageError(206)

elif relay == "valve5":
  if action == "on":
    if relayPins[VALVE5].value == True:
      if verbose == True:
        print("valve5 already on")
    else:
      if verbose == True:
        print("executing " + relay + " " + action)
      if sendsyslog == True:
        syslog.syslog("executing " + relay + " " + action)
      relayPins[VALVE5].value = True
  elif action == "off":
    if relayPins[VALVE5].value == False:
      if verbose == True:
        print("valve5 already off")
    else:
      if verbose == True:
        print("executing " + relay + " " + action)
      if sendsyslog == True:
        syslog.syslog("executing " + relay + " " + action)
      relayPins[VALVE5].value = False
  else:
    usageError(207)

elif relay == "pump1":
  if action == "on":
    if relayPins[PUMP1].value == True:
      if verbose == True:
        print("pump1 already on")
    else:
      if verbose == True:
        print("executing " + relay + " " + action)
      if sendsyslog == True:
        syslog.syslog("executing " + relay + " " + action)
      relayPins[PUMP1].value = True
  elif action == "off":
    if relayPins[PUMP1].value == False:
      if verbose == True:
        print("pump1 already off")
    else:
      if verbose == True:
        print("executing " + relay + " " + action)
      if sendsyslog == True:
        syslog.syslog("executing " + relay + " " + action)
      relayPins[PUMP1].value = False
  else:
    usageError(208)

elif relay == "pump2":
  if action == "on":
    if relayPins[PUMP2].value == True:
      if verbose == True:
        print("pump2 already on")
    else:
      if verbose == True:
        print("executing " + relay + " " + action)
      if sendsyslog == True:
        syslog.syslog("executing " + relay + " " + action)
      relayPins[PUMP2].value = True
  elif action == "off":
    if relayPins[PUMP2].value == False:
      if verbose == True:
        print("pump2 already off")
    else:
      if verbose == True:
        print("executing " + relay + " " + action)
      if sendsyslog == True:
        syslog.syslog("executing " + relay + " " + action)
      relayPins[PUMP2].value = False
  else:
    usageError(209)

elif relay == "test":
  if action == "on":
    if verbose == True:
      print("executing " + relay + " " + action)
    if sendsyslog == True:
      syslog.syslog("executing " + relay + " " + action)
    for i in range(testcount):
      for p in range(7):
        if verbose == True:
          print("cycle " + str(i) + " pin" + str(p) + " on")
        if sendsyslog == True:
          syslog.syslog("cycle " + str(i) + " pin" + str(p) + " on")
        relayPins[p].value = True  # GPIO0 / GPIOA0 to high logic level
        time.sleep(testontime)
        if verbose == True:
          print("cycle " + str(i) + " pin" + str(p) + " off")
        if sendsyslog == True:
          syslog.syslog("cycle " + str(i) + " pin" + str(p) + " off")
        relayPins[p].value = False # GPIO0 / GPIOA0 to low logic level
        time.sleep(testofftime)
    
  else:
    usageError(210)

else:
  usageError(211)
