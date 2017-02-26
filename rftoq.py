#!/usr/bin/env python

# rftoq.py  -  Capture any RF messages and push them to MQTT queue

 
# ToDo

import os
import sys
import time
#from datetime import datetime
#import pytz
#import tzlocal
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt

from nrf24 import NRF24

##STATUSCAKE_URL="https://push.statuscake.com/?PK=50bc5a406146489&TestID=510385"
##PUSHMON_URL="http://ping.pushmon.com/pushmon/ping/"
##PUSHMON_ID="WmpnHI"
##PUSHINGBOX_URL="http://api.pushingbox.com/pushingbox"
##PUSHINGBOX_ID="vF6098C58E4A4D96"
#GROVESTREAMS_URL = "http://grovestreams.com/api/feed?asPut&api_key=521dfde4-e9e2-36b6-bf96-18242254873f"

#DEFAULT_API_KEY = "IjPjyGRBNX4215uvu7sAB86NBjCtklQByFAIb1VoJT2TUeXF"
#DEFAULT_FEED_ID = "1785749146"

#Q_BROKER="m11.cloudmqtt.com"
#Q_PORT=19873
#Q_USER="prcegtgc"
#Q_PSWD="7frPa1U_VXqA"
Q_BROKER="127.0.0.1"
Q_PORT=1883
Q_TOPIC="hello"

IsConnected=False
IsCnxnErr=False

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

def on_connect(client, userdata, flags, rc):
    global IsConnected,IsCnxnErr
    print("CB: Connected;rtn code [%d]"% (rc) )
    if( rc == 0 ):
        IsConnected=True
    else:
        IsCnxnErr=True

def on_disconnect(client, userdata, rc):
    global IsConnected
    print("CB: Disconnected with rtn code [%d]"% (rc) )
    IsConnected=False

def on_publish(client,userdata,mid):
    print("Data Published, Msg ID: [%d]" % mid)
    pass

def on_log(client, userdata, level, buf):
    print("log: ",buf)


# main program entry point - runs continuously updating our datastream with the
def run( client ):

  init_GPIO()
  initRadioReceive()

  client.on_publish = on_publish
  client.on_connect = on_connect
  client.on_disconnect = on_disconnect
#  client.on_log = on_log
#  client.username_pw_set(Q_USER, Q_PSWD)

  client.connect(Q_BROKER, Q_PORT, keepalive=60)
  client.loop_start()

  retry=0
  while( (not IsConnected) and (not IsCnxnErr) and retry <= 10):
      print("Waiting for Connect")
      time.sleep(.05)
      retry += 1
  if( not IsConnected or IsCnxnErr ):
      print("No connection could be established")
      return

  #while True and IsConnected:
  while True:
    pipe = [1]
    while( radio.available(pipe, False) ):
        recv_buffer = []
        recv_string = ""
        #myDateTime = datetime.utcnow().replace(tzinfo=pytz.utc);

        radio.read(recv_buffer)
        for x in recv_buffer:
            recv_string += chr(x)
	print "RF Msg received: [%s]" % recv_string

        if( not IsConnected ):
            print( "ERROR: RF Msg received; NO CONNECTION to queue" )
        client.publish(Q_TOPIC,recv_string, 1)

    radio.startListening()

    sys.stdout.flush()
    time.sleep(SLEEP_SECONDS)
 
try:
    client = mqtt.Client("rftoq")
    run(client)
except KeyboardInterrupt:
    print "Keyboard Interrupt..."
finally:
    print "Exiting."

    time.sleep(.25)
    client.disconnect()
    while( IsConnected ):
        print("Waiting for Disconnect")
        time.sleep(.05)
    client.loop_stop()

    GPIO.cleanup()

