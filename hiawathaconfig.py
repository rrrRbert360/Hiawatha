############################################
#
# The variables in this file are read by the main program Hiawatha. (hw.py)
# Please notice that YOU MUST enter for own data in this file where the word 'replace' is mentioned. 
#
#    This file is part of Hiawatha.


############################################
#
# YOU MUST ENTER THE SPECIFIC ASSET DETAILS/CREDENTIALS HERE:
#
assetID = 'replace_this_by_the_AssetName'	# Use a single name without space or special characters like '!@#$%$%|[^%&*):-';"?! etc.





############################################
#
# FOR A QUICKSTART, IGNORE EVERYTHING HERE BELOW


MTBHB = 900      	# time mqtt messages (default value is 900 which equals 15 minutes)
MinSensorloops = 3 
RebootEnabled = 0	# allows this system to auto-reboot after failing to ping test the Testhosts below



############################################
#
# Definition of connectivity test hosts of
# which at least 1 must return with
# ICMP ping replies 
#
Testhost1 = "8.8.8.8" # replace these public ping-test IP-addresses if your are using a private mobile network 
Testhost2 = "8.8.8.8" # It is better to use two different hostst to ping tests to prevent false positive of connection-validation when a host times out. So yes, please replace



############################################
#
# Asset related MQTT credentials 
#
MQTTurl = "replace_this_by_the_MQTT_topic"			# MQTT broker host name e.g. m20.cloudmqtt.com, if your are on a prive network check DNS or use /etc/hosts
MQTTtpc = "replace_this_by_the_MQTT_topic"          # MQTT broker topic name
MQTTusr = "replace_this_by_the_user_name"           # MQTT broker subscriber name
MQTTpwd = "replace_this_by_the_user_password"       # password related to the MQTT broker subscriber
MQTTprt = "18384"                                   # port number of the MQTT broker




configfileversion = 1
