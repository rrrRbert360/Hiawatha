#!/bin/sh
#
# This batch file launches the main python3 program hw.py
# All files must be located in ~/home/pi 
# This file needs to be called from the batch-file which is executed after powering up /etc/rc.local (you have to edit&add a refer to this launcher.sh)
#
sleep 15
cd home/pi
sudo python3 hw.py


