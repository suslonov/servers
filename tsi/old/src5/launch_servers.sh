#!/bin/bash

#   Uncomment to kill the processes after the script ends
#trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

python3.5 ./KYC_server.py 2>&1 kyc_log.log | tee -a &
python3.5 ./TSUA_server.py 2>&1 tsua_log.log | tee -a 

#   Kill the script after 30 min if not killed by the user
#sleep 30m

