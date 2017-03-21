#!/usr/bin/env python

# rftoqueue.py  -  Capture any RF messages and push them to MQTT queue

 
# ToDo

import os
import sys
import time
import re

import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import ConfigParser

from nrf24 import NRF24

# ---- Globals ----
IsConnected=False
cnxnRC=-1

##  RF Read Code
pipes = [[0xF0, 0xF0, 0xF0, 0xF0, 0xE1], [0xF0, 0xF0, 0xF0, 0xF0, 0xD1]]

SLEEP_SECONDS = 1 
config = None

radio = NRF24()

# ----------------------------------------------------------------
def getConfigExt( configSysIn, sectionIn, optionIn, defaultIn=None ):
    optionOut=defaultIn
    if( configSysIn.has_option( sectionIn, optionIn)):
        optionOut = configSysIn.get(sectionIn, optionIn)
    return optionOut

def getConfigExtBool( configSysIn, sectionIn, optionIn, defaultIn=False ):
    optionOut=defaultIn
    if( configSysIn.has_option( sectionIn, optionIn)):
        optionOut = configSysIn.getboolean(sectionIn, optionIn)
    return optionOut


def init_GPIO():
    GPIO.setmode(GPIO.BCM)

def initRadioReceive():
    radio.begin(0, 0, config.getint("DEFAULT", "CE_PIN_"), config.getint("DEFAULT", "IRQ_PIN_") )

    #radio.setDataRate(NRF24.BR_1MBPS)
    radio.setDataRate(NRF24.BR_250KBPS)
    radio.setPALevel(NRF24.PA_MAX)
    radio.setChannel( config.getint("DEFAULT", "RF_CHANNEL") )
    radio.setRetries(15,15)
    radio.setAutoAck(0)
    radio.setPayloadSize(config.getint("DEFAULT", "PAYLOAD_SIZE"))
    ##radio.enableDynamicPayloads()

    radio.openWritingPipe(pipes[0])
    radio.openReadingPipe(1, pipes[1])

    radio.startListening()
    radio.stopListening()
    radio.printDetails()
    print "-"*40

    radio.startListening()

def on_connect(client, userdata, flags, rc):
    global IsConnected, cnxnRC
    print("CB: Connected;rtn code [%d]"% (rc) )
    cnxnRC=rc
    if( rc == 0 ):
        IsConnected=True

def on_disconnect(client, userdata, rc):
    global IsConnected
    print("CB: Disconnected with rtn code [%d]"% (rc) )
    IsConnected=False

def on_publish(client,userdata,mid):
    if( getConfigExtBool(config, "DEFAULT", 'debug') ):
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
  if( getConfigExtBool(config, "DEFAULT", 'qlog_enable') ):
      client.on_log = on_log

  if( getConfigExt(config, "DEFAULT", 'user', None) and getConfigExt(config, "DEFAULT", 'pswd', None) ):
      print( "Setting User and pswd")
      client.username_pw_set( config.get("DEFAULT", 'user'), config.get("DEFAULT", 'pswd') )

  client.connect(config.get("DEFAULT", 'broker'), config.get("DEFAULT", 'port'), 60)
  client.loop_start()

  retry=0
  while( (not IsConnected) and cnxnRC == -1 and retry <= 10):
      print("Waiting for Connect")
      time.sleep(.05)
      retry += 1
  if( not IsConnected ):
      print("No connection could be established: rc[%d]") % cnxnRC
      return

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

        if( re.search('[^\x00-\x7F]', recv_string) is not None ):
            print ("[%s] not ascii" % recv_string)
            continue

        if( len(recv_string)  < 18 ):
            print ("[%s] is too short" % recv_string)
            continue
        else:
            print ("long enough")

        if( not IsConnected ):
            print( "ERROR: RF Msg received; NO CONNECTION to queue" )
        else:
            try:
                info=client.publish(config.get("DEFAULT", 'topic'), recv_string, qos=1)
                if( info[0] == mqtt.MQTT_ERR_SUCCESS ):
                    info.wait_for_publish()
                else:
                    print( "ERROR: Publish call returned %d") % info[0]
            except UnicodeDecodeError as err:
                print "An exception occurred when publishing Q message [%s]" % recv_string
                print "-----  BEGIN EXCEPTION TRACEBACK -----"
                print err
                print "-----  END EXCEPTION TRACEBACK -----"

    radio.startListening()

    sys.stdout.flush()
    time.sleep(SLEEP_SECONDS)
 
# -------------------------------------

client = mqtt.Client("rftoqueue")

try:
    configFile=os.path.splitext(__file__)[0]+".conf"
    if( not os.path.isfile( configFile )):
        print( "Config file [%s] was not found.  Exiting" ) % configFile
        exit()

    config = ConfigParser.SafeConfigParser()
    config.read(configFile)
    if( getConfigExtBool(config, "DEFAULT", 'debug') ):
        print("Using config file [%s]") % configFile

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

