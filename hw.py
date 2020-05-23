#!/usr/bin/python3.4
# -*- coding: utf-8 -*-
#
# Hiawatha Proof Of Concept 
# Robert J. Heerekop IOTC360.COM
#
# This program is launched from the shell script launcher.sh
#
currentversion = "23052020"
#
# This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Notes on this programme: It needs to be placed in /home/pi and requires following files:
# /home/pi/hiawathaconfig.py    <- please also open and read comment in this file
# /home/pi/mqttpost.sh          <- please also open and read comment in this file
#
# Notes:
# This code uses a AD-convertor conencted to the SPI interface.
# Enable SPI interface by configuring 'sudo raspi-config'
# To use SPI interface enter 'sudo pip3 install spidev'
#
# Data output example:
# A reported MQTT JSON string wil for example look like this:
# {"AssetID":"PoC1","SensorValue":"14220","SensorStatus":"1","Version":"16052020","Uptime":"72528","Tbd":"tbd"}
#              ^                    ^                     ^                  ^               ^           ^
#              |                    |                     |                  |               |      for future use
#            AssetID      measured loop current     1=sensor read valid     sw-version      uptime 
#                                 in mA            0=sensor read NOT valid                  in sec.
#
import os
import random
import sys
import time
import logging
import RPi.GPIO as GPIO
import spidev
from time import sleep
from subprocess import check_output
import socket
import fcntl
import struct
import psutil


#####################################################################################################################################################################
#
# Specific settings for your project are read from the file hiawathaconfig.py
# PLEASE ENSURE to put your own settings in that file!
# YOU MUST EDIT THE FILE hiawathaconfig.py BEFORE USING THIS PROGRAMME. Use a text editor.
#
Requiredconfigfileversion = 1                   # this is variable used to verify the format version of the to be imported file hiawathaconfig.py
import hiawathaconfig				# read variables from config file


#####################################################################################################################################################################
#
# This function is to read the A/D converter using the SPI bus
#
#
class MCP3201(object):
    """
    
    """
    def __init__(self, SPI_BUS, CE_PIN):
        """
        initializes the device, takes SPI bus address (which is always 0 on newer Raspberry models)
        and sets the channel to either CE0 = 0 (GPIO pin BCM 8) or CE1 = 1 (GPIO pin BCM 7)
        """
        if SPI_BUS not in [0, 1]:
            raise ValueError('wrong SPI-bus: {0} setting (use 0 or 1)!'.format(SPI_BUS))
        if CE_PIN not in [0, 1]:
            raise ValueError('wrong CE-setting: {0} setting (use 0 for CE0 or 1 for CE1)!'.format(CE_PIN))
        self._spi = spidev.SpiDev()
        self._spi.open(SPI_BUS, CE_PIN)
        self._spi.max_speed_hz = 976000
        pass

    def readADC_MSB(self):
        """
        Reads 2 bytes (byte_0 and byte_1) and converts the output code from the MSB-mode:
        byte_0 holds two ?? bits, the null bit, and the 5 MSB bits (B11-B07),
        byte_1 holds the remaning 7 MBS bits (B06-B00) and B01 from the LSB-mode, which has to be removed.
        """
        bytes_received = self._spi.xfer2([0x00, 0x00])

        MSB_1 = bytes_received[1]
        MSB_1 = MSB_1 >> 1  # shift right 1 bit to remove B01 from the LSB mode

        MSB_0 = bytes_received[0] & 0b00011111  # mask the 2 unknown bits and the null bit
        MSB_0 = MSB_0 << 7  # shift left 7 bits (i.e. the first MSB 5 bits of 12 bits)

        return MSB_0 + MSB_1


    def readADC_LSB(self):
        """
        Reads 4 bytes (byte_0 - byte_3) and converts the output code from LSB format mode:
        byte 1 holds B00 (shared by MSB- and LSB-modes) and B01,
        byte_2 holds the next 8 LSB bits (B03-B09), and
        byte 3, holds the remaining 2 LSB bits (B10-B11).
        """
        bytes_received = self._spi.xfer2([0x00, 0x00, 0x00, 0x00])

        LSB_0 = bytes_received[1] & 0b00000011  # mask the first 6 bits from the MSB mode
        LSB_0 = bin(LSB_0)[2:].zfill(2)  # converts to binary, cuts the "0b", include leading 0s

        LSB_1 = bytes_received[2]
        LSB_1 = bin(LSB_1)[2:].zfill(8)  # see above, include leading 0s (8 digits!)

        LSB_2 = bytes_received[3]
        LSB_2 = bin(LSB_2)[2:].zfill(8)
        LSB_2 = LSB_2[0:2]  # keep the first two digits

        LSB = LSB_0 + LSB_1 + LSB_2  # concatenate the three parts to the 12-digits string
        LSB = LSB[::-1]  # invert the resulting string
        return int(LSB, base=2)

        


#####################################################################################################################################################################
#
# This function is turn the light to record  on or off.
#
#
def LedTurn(LedAction):
    if LedAction == "off":
        GPIO.output(17,GPIO.LOW)
    if LedAction == "on":
        GPIO.output(17,GPIO.HIGH)


#####################################################################################################################################################################
#
# This function blinks the led which indicates status of two given variables StatusA, StatusB):
# Short blink = 0
# Long blink = 1
#
#
def LedBlink(StatusA, StatusB):
    period = 0.1
    LedTurn("on")
    if StatusA == 1: sleep(period)
    if StatusA == 0: sleep(period * 3)
    LedTurn("off")
    sleep(period * 3)
    LedTurn("on")
    if StatusB == 1: sleep(period)
    if StatusB == 0: sleep(period * 3)
    LedTurn("off")




#####################################################################################################################################################################
#
# This function is similar to sleep() but during the sleep perio is blinks a gpio status led
# Usage: e.g. LEDStatusPause(10,1,0)   which results in a sleep of 10 seconds with 3s intervals
#        filled with short and long blink.
#
def seconds_elaspsed():
    return time.time() - psutil.boot_time()
def LEDStatusPause(t, StatusA, StatusB):
    starttime = seconds_elaspsed()
    currenttime = starttime
    while (currenttime < (starttime +t)):
        LedBlink(StatusA,StatusB)
        sleep(2)
        currenttime = seconds_elaspsed()



#####################################################################################################################################################################
#
# This function is used to test if there is an IP-connection
# by 10 times pinging a host.
# If at least 1 ping is returned the Internetstatus = 1
# The packetloss indicates the percentage of lost packets 
#
def TestWAN(url):
    global COMMStatus
    InternetStatus = 1
    InternetStatus = 99
    packetloss = 100
    try:
     response = 5
     outstring = str(check_output(["ping", "-c" , "10", url]))
     InternetStatus = 1
     COMMStatus = 1
     str2 = "packet loss";
     str1 = "received";
     rpointer=(outstring.find(str2, 0, len(outstring))) - 2
     if rpointer > -1 :
      lpointer=(outstring.find(str1, 0, len(outstring))) + len(str1) + 2
      packetloss = int((outstring[lpointer:rpointer]))
    except:
     InternetStatus = 0
     COMMStatus = 0
    return InternetStatus, packetloss



#####################################################################################################################################################################
#
# This function resets and tests the LAN eth0 interface
# If a the test does not work out it also reboots(!) the system 
#
# Note: if DHCP does not work properly during duration tests it might be worth 
#       investigating to add 'sudo dhclient -v eth0' command after a 'if up'
#
def ResetLAN():
    global COMMStatus
    COMMStatus = 0
    OSString = 'sudo ip link set eth0 down' 
    logging.info(OSString)
    os.system(OSString)
    LEDStatusPause(2,1,COMMStatus)
    OSString = 'sudo ip link set eth0 up' 
    logging.info(OSString)
    os.system(OSString)
    logging.info("wait... lan-eth reset done, connection testing again...")
    LEDStatusPause(60,1,COMMStatus)
    LANip = ReadIP("eth0")
    logging.info("eth0=" + LANip)
    ConnectionTesthost1, packetloss = TestWAN(hiawathaconfig.Testhost1) 
    ConnectionTesthost2, packetloss = TestWAN(hiawathaconfig.Testhost2)
    WANConnection = ConnectionTesthost1 + ConnectionTesthost2
    logging.info("IP-test hosts sucesfully pinged=" + str(WANConnection))
    if (WANConnection == 0) and (hiawathaconfig.RebootEnabled == 1) :
        OSString = 'sudo reboot'
        print(OSString)
        logging.info(OSString)
        os.system(OSString)
    if (WANConnection == 0) and (hiawathaconfig.RebootEnabled == 0) :
        logging.info("eth0:" + ReadIP("eth0"))
        logging.info("lan-eth reset does not resolve connection problem. Configfile hiawathaconfig.py does ot allow to reboot")
    if (WANConnection > 0) :
         COMMStatus = 1 
         logging.info("lan-eth connection re-established")


#####################################################################################################################################################################
#
# This function is used to return a string with nework interface IP-details 
#
def ReadIP(interface):
    InternetStatus = 1
    outstring = str(check_output(["ifconfig"]))
    LANdetails = ""
    str1 = interface
    str2 = "inet"
    str3 = "broadcast"
    lpointer=(outstring.find(str1, 0, len(outstring)))
    if lpointer > -1 :
     rpointer = (outstring.find(str2, lpointer, len(outstring)))
     frpointer = (outstring.find(str3, lpointer, len(outstring)))
     LANdetails = outstring[rpointer:frpointer]
    return LANdetails


#####################################################################################################################################################################
#
# Read sensor
#
#
def ReadSensor():
    sensorstatus = 0
    try :
      ADC_MSB_output_code = MCP3201.readADC_MSB()
      sleep(0.1)  # wait minimum of 100 ms between ADC measurements
      ADC_LSB_output_code = MCP3201.readADC_LSB()    
      sensorvalue = (ADC_MSB_output_code + ADC_LSB_output_code ) / 2
    except :
      sensorstatus = 0
    else :
      sensorstatus = 1
      noise = abs(ADC_MSB_output_code - ADC_LSB_output_code)
      if noise > 5 : sensorstatus = 0
    return sensorvalue, sensorstatus




####################################################################################################################################################################
#
# Sheduled heartbeat reporting
#
# Generates and executes a shell command string like:
# pi@raspberrypi:~ $ /home/pi/mqttpost.sh [mqtt host] [mqtt topic] [mqtt user] [mqtt password] [mqtt port] Arg1 Arg2 arg3 Arg4 Arg5 Arg6
#
def SheduledReport(MQTTArg1, MQTTArg2, MQTTArg3, MQTTArg4, MQTTArg5, MQTTArg6):
    global MQTTurl
    global MQTTtpc
    global MQTTusr
    global MQTTpwd
    global MQTTprt
    OSString = '/home/pi/mqttpost.sh ' + MQTTurl + ' ' + MQTTtpc + ' ' + MQTTusr + ' ' + MQTTpwd + ' ' + MQTTprt + ' ' + MQTTArg1 + ' ' + MQTTArg2 + ' ' + MQTTArg3 + ' ' + MQTTArg4 + ' ' + MQTTArg5 + ' ' + MQTTArg6 
    logging.info(OSString)
    os.system(OSString) 


#####################################################################################################################################################################
#
# Create and shift log-files
#
os.system ('mv previous.log preprevious.log')
os.system ('mv current.log previous.log')
formatter = logging.Formatter('%(message)s')
logging.getLogger('').setLevel(logging.DEBUG)
fh = logging.FileHandler('current.log')
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logging.getLogger('').addHandler(fh)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logging.getLogger('').addHandler(ch)


#####################################################################################################################################################################
#
# Start initialization
#
#####################################################################################################################################################################
#
# Set GPIO outputs to power leds and sensor
#
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(17,GPIO.OUT) # led light

logging.info("Starting...reading config file /home/pi/hiawathaconfig.py")
logging.info("This is:" + hiawathaconfig.assetID)
logging.info("sw = %s " % currentversion)
logging.info("hiawathaconfig.MTBHB=%s" % str(hiawathaconfig.MTBHB) )
logging.info("Test ping host1:" + hiawathaconfig.Testhost1)
logging.info("Test ping host2:" + hiawathaconfig.Testhost2)
logging.info("eth0:" + ReadIP("eth0"))


#####################################################################################################################################################################
#
# Run some initialization code before we loop
#
if (len(hiawathaconfig.assetID) == 0):
    print ("\n\nSTOP! Before you start this programme you need to enter your projectname etc in the source config .py code file!\n\n")
    raw_input('Press CTRL+C to quit')

if ( hiawathaconfig.configfileversion != Requiredconfigfileversion):
    print ("\n\nSTOP! The version of the file hiawathaconfig.py does not match which the version this program needs and is not compatible!")
    raw_input('Press CTRL+C to quit')

#####################################################################################################################################################################
#
# Read asset related MQTT credentials from config file
#
MQTTurl = hiawathaconfig.MQTTurl
MQTTtpc = hiawathaconfig.MQTTtpc
MQTTusr = hiawathaconfig.MQTTusr
MQTTpwd = hiawathaconfig.MQTTpwd
MQTTprt = hiawathaconfig.MQTTprt


COMMStatus = 0 # flag indicating if ping test is successful. This is used for LED indication



#####################################################################################################################################################################
#
# Power on sensor
#
#SwitchSensor("off")                                         #for future use, power off sensor emitter (just in case it was on after a reboot)
logging.info("Power on sensor" )
#SwitchSensor("on")

LedTurn("off")

if __name__ == '__main__':
    SPI_bus = 0
    CE = 0
    MCP3201 = MCP3201(SPI_bus, CE)
    
    try:
        while True:
            LedTurn("on")
            SensorValue, SensorStatus = ReadSensor()
            if (SensorStatus == 0): logging.info("Sensor problem")
            ConnectionTesthost1, packetloss = TestWAN(hiawathaconfig.Testhost1) 
            ConnectionTesthost2, packetloss = TestWAN(hiawathaconfig.Testhost2)
            WANConnection = ConnectionTesthost1 + ConnectionTesthost2
            if (WANConnection > 0):
                systemuptimesec = str(seconds_elaspsed()).split(".")[0]
                MultipliedValue = round(1000 * float((SensorValue + 35) / 200))
                SheduledReport(hiawathaconfig.assetID, str(MultipliedValue), str(SensorStatus), currentversion, systemuptimesec, "tbd")
            else:
                ResetLAN()
            LEDStatusPause(hiawathaconfig.MTBHB,1,COMMStatus)
            print("next loop")

    except (KeyboardInterrupt):
        print('\n', "Exit on Ctrl-C: Good bye!")

    except:
        print("Other error or exception occurred!")
        raise

