#!/bin/bash 

# start  paas-api  bash 

#start a timers 
nohup python cacheThead.py > cache.log 2>&1  

#start api 
python paas-api.py 0.0.0.0 8080 & 
