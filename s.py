#!/usr/bin/env python

import paho.mqtt.client as mqtt

mqttc = mqtt.Client("python_pub")
mqttc.username_pw_set("prcegtgc", "7frPa1U_VXqA")
mqttc.connect("m11.cloudmqtt.com", 19873)
mqttc.publish("hello", "Hello, World!")
mqttc.loop(2)
