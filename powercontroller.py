#!/usr/bin/python3
#
# powercontroller.py
#
# Copyright 2022 Allen Pomeroy
#
# version: 1.1
#
# v1.1
# - add read of pin value prior to set
# v1.0
# - initial release
#
# Control script for Allen Pomeroy PowerController hardware v2.3
# MCP23017 based I2C bus expansion board
# - 5x 24VAC valve relays
# - 2x 12VDC pump relay feeds
# - 3x 5v GPIO digital lines
# - AC Hz sensor
# 
# Turns pump or valve relays on or off
#
# PowerController i2c bus address jumpers
#  A2 A1 A0
#  0  0  0  0x20
#  0  0  1  0x21
#  0  1  0  0x22
#  0  1  1  0x23
#  1  0  0  0x24
#
# Hardware I/O configuration
# GPIO_B0 pin8  valve1
# GPIO_B1 pin9  valve2
# GPIO_B2 pin10 valve3
# GPIO_B3 pin11 valve4
# GPIO_B4 pin12 valve5
# GPIO_A0 pin0  pump1
# GPIO_A1 pin1  pump2
#
# GPIO_INTA acsense
#
# GPIO_B5 pin13 line0
# GPIO_B6 pin14 line1
# GPIO_B7 pin15 line2
#
# Usage:
# powercontroller.py {relay-name|all} {on|off}
# valve1, valve2, valve3, valve4, valve5, pump1, pump2, test
# 
# Optionally can specify "all" for relay name for "off" action.
# Can specify "test" "on" to run a loop through each relay activated
# sequentially TESTCOUNT times.
#

# imports
import board
import busio
import time
import configparser
from array import array
import sys
from digitalio import Direction
from adafruit_mcp230xx.mcp23017 import MCP23017

# config file for options
config = configparser.ConfigParser()
config.read('powercontroller.conf')

# default constants
I2CADDR = 0x24 # A2=1, A1=0, A0=0
TESTCOUNT = 3
TESTONTIME = 1
TESTOFFTIME = 0.1

# GPIO Pin Layout - PCB and Breadboard
#
# GPIO-ID  PIN  IC-PIN  HW     BREADBOARD
# GPIOA0   0    21      PUMP1  RED
# GPIOA1   1    22      PUMP2  YEL
# GPIOA2   2    23             GREEN
# GPIOA3   3    24             BLUE
# GPIOA4   4    25      
# GPIOA5   5    26      
# GPIOA6   6    27      
# GPIOA7   7    28      
# GPIOB0   8     1      VALVE1  RELAY
# GPIOB1   9     2      VALVE2
# GPIOB2   10    3      VALVE3
# GPIOB3   11    4      VALVE4
# GPIOB4   12    5      VALVE5
# GPIOB5   13    6      LINE0
# GPIOB6   14    7      LINE1
# GPIOB7   15    8      LINE2

# PCB
#VALVE1PIN = 8  # GPIO_B0 valve1
#VALVE2PIN = 9  # GPIO_B1 valve2
#VALVE3PIN = 10 # GPIO_B2 valve3
#VALVE4PIN = 11 # GPIO_B3 valve4
#VALVE5PIN = 12 # GPIO_B4 valve5
#PUMP1PIN  = 0  # GPIO_A0 pump1
#PUMP2PIN  = 1  # GPIO_A1 pump2

# Breadboard
VALVE1PIN = 8
VALVE2PIN = 0
VALVE3PIN = 1
VALVE4PIN = 2
VALVE5PIN = 3
PUMP1PIN  = 8
PUMP2PIN  = 2

# array index
VALVE1 = 0
VALVE2 = 1
VALVE3 = 2
VALVE4 = 3
VALVE5 = 4
PUMP1  = 5
PUMP2  = 6

# --------------
# error handlers

# usage error
def usageError(errno):
  print("usage: powercontroller.py {relay-name|all} {on|off} error code " + str(errno))
  print("relay-name can be \"all\" for \"off\" action only")
  print("valve1  valve2  valve3  valve4  valve5  pump1  pump2  test")
  exit(1)

# error exit
def initError(errno):
  print("powercontroller.py initialization error code " + str(errno))
  exit(errno)

# ----
# setup i2c handle and access

try:
  i2c = busio.I2C(board.SCL, board.SDA)
except ValueError:
  initError(301)

# create MCP access
try:
  mcp = MCP23017(i2c,address=I2CADDR)
except ValueError:
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

# set all the port B line pins to input, with pullups
#for pin in port_b_pins:
#    pin.direction = Direction.INPUT
#    pin.pull = Pull.UP

#pin0.value = True  # GPIO0 / GPIOA0 to high logic level
#pin0.value = False # GPIO0 / GPIOA0 to low logic level


# must be three arguments
if len(sys.argv) != 3  or (sys.argv[2] != "on" and sys.argv[2] != "off"):
  usageError(201)

# capture relay and action from command line arguments
relay  = sys.argv[1]
action = sys.argv[2]

# check arguments
if relay == "all":
  if action == "off":
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
      print("valve1 already on")
    else:
      print("turning valve1 on")
      relayPins[VALVE1].value = True
    #print("current value of valve1 = {0}".format(relayPins[VALVE1].value))
  elif action == "off":
    if relayPins[VALVE1].value == False:
      print("valve1 already off")
    else:
      print("turning valve1 off")
      relayPins[VALVE1].value = False
  else:
    usageError(203)

elif relay == "valve2":
  if action == "on":
    if relayPins[VALVE2].value == True:
      print("valve2 already on")
    else:
      print("turning valve2 on")
      relayPins[VALVE2].value = True
  elif action == "off":
    if relayPins[VALVE2].value == False:
      print("valve2 already off")
    else:
      print("turning valve2 off")
      relayPins[VALVE2].value = False
  else:
    usageError(204)

elif relay == "valve3":
  if action == "on":
    if relayPins[VALVE3].value == True:
      print("valve3 already on")
    else:
      print("turning valve3 on")
      relayPins[VALVE3].value = True
  elif action == "off":
    if relayPins[VALVE3].value == False:
      print("valve3 already off")
    else:
      print("turning valve3 off")
      relayPins[VALVE3].value = False
  else:
    usageError(205)

elif relay == "valve4":
  if action == "on":
    if relayPins[VALVE4].value == True:
      print("valve4 already on")
    else:
      print("turning valve4 on")
      relayPins[VALVE4].value = True
  elif action == "off":
    if relayPins[VALVE4].value == False:
      print("valve4 already off")
    else:
      print("turning valve4 off")
      relayPins[VALVE4].value = False
  else:
    usageError(206)

elif relay == "valve5":
  if action == "on":
    if relayPins[VALVE5].value == True:
      print("valve5 already on")
    else:
      print("turning valve5 on")
      relayPins[VALVE5].value = True
  elif action == "off":
    if relayPins[VALVE5].value == False:
      print("valve5 already off")
    else:
      print("turning valve5 off")
      relayPins[VALVE5].value = False
  else:
    usageError(207)

elif relay == "pump1":
  if action == "on":
    if relayPins[PUMP1].value == True:
      print("pump1 already on")
    else:
      print("turning pump1 on")
      relayPins[PUMP1].value = True
  elif action == "off":
    if relayPins[PUMP1].value == False:
      print("pump1 already off")
    else:
      print("turning pump1 off")
      relayPins[PUMP1].value = False
  else:
    usageError(208)

elif relay == "pump2":
  if action == "on":
    if relayPins[PUMP2].value == True:
      print("pump2 already on")
    else:
      print("turning pump2 on")
      relayPins[PUMP2].value = True
  elif action == "off":
    if relayPins[PUMP2].value == False:
      print("pump2 already off")
    else:
      print("turning pump2 off")
      relayPins[PUMP2].value = False
  else:
    usageError(209)

elif relay == "test":
  if action == "on":
    for i in range(TESTCOUNT):
      for p in range(7):
        print("cycle " + str(i) + " pin" + str(p) + " on")
        relayPins[p].value = True  # GPIO0 / GPIOA0 to high logic level
        time.sleep(TESTONTIME)
        print("cycle " + str(i) + " pin" + str(p) + " off")
        relayPins[p].value = False # GPIO0 / GPIOA0 to low logic level
        time.sleep(TESTOFFTIME)
    
  else:
    usageError(210)

else:
  usageError(211)
