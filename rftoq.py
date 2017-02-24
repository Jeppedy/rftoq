#!/usr/bin/env python

# rftoq.py  -  Capture any RF messages and push them to MQTT queue

 
# ToDo

import os
import sys
import time
from datetime import datetime
import pytz
import tzlocal
import requests
import json
import RPi.GPIO as GPIO
import sqlite3
import paho.mqtt.client as mqtt

from nrf24 import NRF24

##STATUSCAKE_URL="https://push.statuscake.com/?PK=50bc5a406146489&TestID=510385"
##PUSHMON_URL="http://ping.pushmon.com/pushmon/ping/"
##PUSHMON_ID="WmpnHI"
##PUSHINGBOX_URL="http://api.pushingbox.com/pushingbox"
##PUSHINGBOX_ID="vF6098C58E4A4D96"

GROVESTREAMS_URL = "http://grovestreams.com/api/feed?asPut&api_key=521dfde4-e9e2-36b6-bf96-18242254873f"

DBLOCATION="/media/nas-rpi/TempMonData/rfmonDB.db"

DEFAULT_API_KEY = "IjPjyGRBNX4215uvu7sAB86NBjCtklQByFAIb1VoJT2TUeXF"
DEFAULT_FEED_ID = "1785749146"

Q_BROKER="m11.cloudmqtt.com"
Q_PORT=19873
Q_TOPIC="hello"

# REMEMBER: OneWire is ALWAYS on Pin #4

##  RF Read Code
pipes = [[0xF0, 0xF0, 0xF0, 0xF0, 0xE1], [0xF0, 0xF0, 0xF0, 0xF0, 0xD1]]
CE_PIN_       = 25  #18
IRQ_PIN_      = 23
RF_CHANNEL    = 76
PAYLOAD_SIZE  = 21

SLEEP_SECONDS = 1 

radio = NRF24()

def init_GPIO():
    GPIO.setmode(GPIO.BCM)

def initRadioReceive():
    radio.begin(0, 0, CE_PIN_, IRQ_PIN_)

    #radio.setDataRate(NRF24.BR_1MBPS)
    radio.setDataRate(NRF24.BR_250KBPS)
    radio.setPALevel(NRF24.PA_MAX)
    radio.setChannel(RF_CHANNEL)
    radio.setRetries(15,15)
    radio.setAutoAck(0)
    radio.setPayloadSize(PAYLOAD_SIZE)
    ##radio.enableDynamicPayloads()

    radio.openWritingPipe(pipes[0])
    radio.openReadingPipe(1, pipes[1])

    radio.startListening()
    radio.stopListening()
    radio.printDetails()
    print "-"*40

    radio.startListening()



# main program entry point - runs continuously updating our datastream with the
def run():

  init_GPIO()
  initRadioReceive()

  while True:
    pipe = [1]
    while( radio.available(pipe, False) ):
        recv_buffer = []
        myDateTime = datetime.utcnow().replace(tzinfo=pytz.utc);

        radio.read(recv_buffer)
	#print "[%s]" % recv_buffer

        doPublish = False


        doPublish = True

        if( doPublish ):
            print "- Updating"

            def on_connect(client, userdata, flags, rc):
                print("Connected with result code [%d]" % rc)

            def on_publish(client,userdata,mid):
                print("Data Published, Msg ID: [%d]" % mid)
                pass

            client = mqtt.Client("rftoq")
            client.on_publish = on_publish
            client.on_connect = on_connect

            client.username_pw_set("prcegtgc", "7frPa1U_VXqA")
            client.connect(Q_BROKER, Q_PORT,  keepalive=60)

            recv_string = ""
            for x in recv_buffer:
                recv_string += chr(x)

            client.publish(Q_TOPIC,recv_string)
            client.disconnect()


            doPublish = False
        else:
            print "- TOO SOON"


    radio.startListening()

    sys.stdout.flush()
    time.sleep(SLEEP_SECONDS)
 
try:
    run()
except KeyboardInterrupt:
    print "Keyboard Interrupt..."
finally:
    print "Exiting."
    GPIO.cleanup()

