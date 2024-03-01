#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys

from yocto_api import YAPI, YSensor, YRefParam
from yocto_serialport import YSerialPort
from yocto_compass import YCompass
from yocto_tilt import YTilt

# DMX512 frame to drive eurolite  LED TMH-46 in 16CH mode
dmxFrame = [ 0, 1, 2, 0, 255, 5, 6, 7, 8, 9, 0, 0, 0, 0, 0, 0, 0, 0, 0  ]

def panCallback(fct, measure):
    dmxFrame[1] = int((405 - measure.get_averageValue()) * 128 / 270)

def tiltCallback(fct, measure):
    dmxFrame[2] = max(int(measure.get_averageValue() * 128 / 90), 0)

def hue2rgb(h):
    h = h & 255
    if h >= 170: return 1
    if h > 42:
        if h <= 127: return 255
        h = 170 - h
    return int(254 * 6 * h / 255) + 1

def hueCallback(fct, measure):
    hue = int(measure.get_averageValue() / 2) + 128
    dmxFrame[6] = hue2rgb(hue + 85)     # R
    dmxFrame[7] = hue2rgb(hue)          # G
    dmxFrame[8] = hue2rgb(hue + 170)    # B

def logfun(line):
    print('LOG : ' + line.rstrip())

# setup the API to use local USB devices
errmsg = YRefParam()
YAPI.RegisterLogFunction(logfun)
if YAPI.RegisterHub("usb", errmsg) != YAPI.SUCCESS:
    sys.exit("RegisterHub error: " + errmsg.value)

# locate Yoctopuce devices
compass = YCompass.FirstCompass()
if compass is None:
    sys.exit("No Yocto-3D-V2 found")
dmxPortOut = YSerialPort.FindSerialPort("DMX-OUT.serialPort")
if not dmxPortOut.isOnline():
    sys.exit("No Yocto-RS485-V2 with logical name DMX-OUT found")

# configure RS485 interface for DMX512 standard
dmxPortOut.set_voltageLevel(YSerialPort.VOLTAGELEVEL_RS485)
dmxPortOut.set_protocol("Frame:2ms")
dmxPortOut.set_serialMode("250000,8N2")

# link orientation sensors to dedicated callback functions
serial = compass.get_serialNumber()
compass.set_bandwidth(20)
compass.set_reportFrequency("20/s")
compass.registerTimedReportCallback(panCallback)
tilt = YTilt.FindTilt(serial+".tilt2")
tilt.set_bandwidth(50)
tilt.set_reportFrequency("50/s")
tilt.registerTimedReportCallback(tiltCallback)
hue = YTilt.FindTilt(serial+".tilt1")
hue.set_reportFrequency("50/s")
hue.set_bandwidth(50)
hue.registerTimedReportCallback(hueCallback)

print('************  DMX512 output demo - hit Ctrl-C to Stop ')

while True:
    # Receive timed report callbacks
    YAPI.Sleep(20, errmsg)
    # Send DMX messages at ~50 Hz
    dmxPortOut.sendBreak(1)
    dmxPortOut.writeArray(dmxFrame)
    print("\b\b\b\b\b\b\b\b\b\b\b\b\b\b{:3d} {:3d} {:3d}".format(dmxFrame[6], dmxFrame[2], dmxFrame[1]), end='')