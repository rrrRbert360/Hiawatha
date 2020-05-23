#!/bin/sh
#
# Sensor MQTT publish Robert J. Heerekop IOTC360
#
# precondition: sudo apt-get install jq
#
# This function is called by the main program with arguments
# This function calls mosquitto_pub which you also(search!) need to install
#
#
MQTTurl=$1	# MQTT Broker
MQTTtpc=$2	# Topic
MQTTusr=$3	# User
MQTTpwd=$4	# Password
MQTTprt=$5	# Port
MQTTArg1=$6	# AssetID
MQTTArg2=$7	# SensorValue
MQTTArg3=$8	# SensorStatus
MQTTArg4=$9	# Version
MQTTArg5=$10	# tbd for future use
MQTTArg6=$11	# tbd for future use

JSON_STRING=$( jq -n -r -c \
                 --arg aid "$MQTTArg1" \
                 --arg svl "$MQTTArg2" \
                 --arg sst "$MQTTArg3" \
                 --arg svr "$MQTTArg4" \
                 --arg tbda "$MQTTArg5" \
                 --arg tbdb "$MQTTArg6" \
                 '{AssetID: $aid, SensorValue: $svl, SensorStatus: $sst, Version: $svr, Uptime: $tbda, Tbd: $tbdb}' )

echo "$JSON_STRING"
mosquitto_pub -h $MQTTurl -t $MQTTtpc -u $MQTTusr -P $MQTTpwd -p $MQTTprt -m $JSON_STRING

