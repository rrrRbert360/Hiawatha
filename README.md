# Hiawatha
RaspberryPi based proof of concept to read an analog sensor and publish its data to a MQTT broker.
This code uses a AD-convertor connected to the SPI interface.

##MQTT data output example
A reported MQTT JSON string wil for example look like this:
{"AssetID":"PoC1","SensorValue":"14220","SensorStatus":"1","Version":"16052020","Uptime":"72528","Tbd":"tbd"}

Asset- and MQTT- specific details must be placed/edited in the configuration file: hiawathaconfig.py
