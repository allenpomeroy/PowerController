#!/usr/bin/python3
#
# power-control.py
#
# version: 1.0
#
# control script for Allen Pomeroy PowerController v2.3
# PowerController i2c bus address
# A2 A1 A0
#  0  0  0  0x20
#  1  0  0  0x24
#
# turns pump or valve relays on or off
#
# power-control.py {relay-name|all} {on|off}
# 
# optionally can specify "all" for relay name for "off" action
#
# valve1, valve2, valve3, valve4, valve5, pump1, pump2

import RPi.GPIO as GPIO
import time
import configparser
from array import array
import sys

config = configparser.ConfigParser()
config.read('/opt/garden/etc/config.txt')

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(int(config['HWv2']['VALVE1']),GPIO.OUT)
GPIO.setup(int(config['HWv2']['VALVE2']),GPIO.OUT)
GPIO.setup(int(config['HWv2']['VALVE3']),GPIO.OUT)
GPIO.setup(int(config['HWv2']['VALVELED1']),GPIO.OUT)
GPIO.setup(int(config['HWv2']['VALVELED2']),GPIO.OUT)
GPIO.setup(int(config['HWv2']['VALVELED3']),GPIO.OUT)

def error_exit(errno):
  print("usage: valve-control.py {valve-name|all} {on|off} error code " + str(errno))
  print("valve-name can be \"all\" for \"off\" action only")
  print("valve1  valve2  valve3")
  exit(1)

if len(sys.argv) != 3  or (sys.argv[2] != "on" and sys.argv[2] != "off"):
  error_exit(201)

valve = sys.argv[1]
action = sys.argv[2]

# check arguments
if valve == "all":
  if action == "off":
    GPIO.output(int(config['HWv2']['VALVE1']),GPIO.LOW)
    GPIO.output(int(config['HWv2']['VALVELED1']),GPIO.LOW)
    GPIO.output(int(config['HWv2']['VALVE2']),GPIO.LOW)
    GPIO.output(int(config['HWv2']['VALVELED2']),GPIO.LOW)
    GPIO.output(int(config['HWv2']['VALVE3']),GPIO.LOW)
    GPIO.output(int(config['HWv2']['VALVELED3']),GPIO.LOW)
  else:
    error_exit(202)

elif valve == "valve1":
  if action == "on":
    GPIO.output(int(config['HWv2']['VALVE1']),GPIO.HIGH)
    GPIO.output(int(config['HWv2']['VALVELED1']),GPIO.HIGH)
    GPIO.output(int(config['HWv2']['VALVE2']),GPIO.LOW)
    GPIO.output(int(config['HWv2']['VALVELED2']),GPIO.LOW)
    GPIO.output(int(config['HWv2']['VALVE3']),GPIO.LOW)
    GPIO.output(int(config['HWv2']['VALVELED3']),GPIO.LOW)
  elif action == "off":
    GPIO.output(int(config['HWv2']['VALVE1']),GPIO.LOW)
    GPIO.output(int(config['HWv2']['VALVELED1']),GPIO.LOW)
  else:
    error_exit(203)

elif valve == "valve2":
  if action == "on":
    GPIO.output(int(config['HWv2']['VALVE1']),GPIO.LOW)
    GPIO.output(int(config['HWv2']['VALVELED1']),GPIO.LOW)
    GPIO.output(int(config['HWv2']['VALVE2']),GPIO.HIGH)
    GPIO.output(int(config['HWv2']['VALVELED2']),GPIO.HIGH)
    GPIO.output(int(config['HWv2']['VALVE3']),GPIO.LOW)
    GPIO.output(int(config['HWv2']['VALVELED3']),GPIO.LOW)
  elif action == "off":
    GPIO.output(int(config['HWv2']['VALVE2']),GPIO.LOW)
    GPIO.output(int(config['HWv2']['VALVELED2']),GPIO.LOW)
  else:
    error_exit(204)

elif valve == "valve3":
  if action == "on":
    GPIO.output(int(config['HWv2']['VALVE1']),GPIO.LOW)
    GPIO.output(int(config['HWv2']['VALVELED1']),GPIO.LOW)
    GPIO.output(int(config['HWv2']['VALVE2']),GPIO.LOW)
    GPIO.output(int(config['HWv2']['VALVELED2']),GPIO.LOW)
    GPIO.output(int(config['HWv2']['VALVE3']),GPIO.HIGH)
    GPIO.output(int(config['HWv2']['VALVELED3']),GPIO.HIGH)
  elif action == "off":
    GPIO.output(int(config['HWv2']['VALVE3']),GPIO.LOW)
    GPIO.output(int(config['HWv2']['VALVELED3']),GPIO.LOW)
  else:
    error_exit(205)

else:
  error_exit(206)
