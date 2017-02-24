#!/usr/bin/env python

# rftoq.py  -  Capture any RF messages and push them to MQTT queue

 
# ToDo

import os
import sys
import time
from datetime import datetime
import pytz
import tzlocal
import paho.mqtt.client as mqtt

Q_BROKER="localhost"
Q_PORT=1883

SLEEP_SECONDS = 10 

# main program entry point - runs continuously updating our datastream with the
def run():

    def on_connect(client, userdata, flags, rc):
        print("Connected with result code "+str(rc))

    def on_disconnect(client,userdata,result):
        print("Disconnected \n")
        pass

    def on_publish(client,userdata,result):
        print("data published \n")
        pass

    client = mqtt.Client("rftoq")
    client.on_publish = on_publish
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.connect(Q_BROKER, Q_PORT, keepalive=60)
    client.loop()

    client.publish("jeff2/","sample message")
    client.loop()
    client.publish("jeff2/","sample message")
    client.loop()
    client.publish("jeff2/","sample message")
    client.loop()
    client.publish("jeff2/","sample message")
    client.loop()
    client.publish("jeff2/","sample message")
    client.loop()

try:
    run()
except KeyboardInterrupt:
    print "Keyboard Interrupt..."
finally:
    print "Exiting."

