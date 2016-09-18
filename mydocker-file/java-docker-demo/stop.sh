#!/bin/bash
javaid=`ps -ef  | grep java  |grep -v  grep | awk '{print $2}'`
kill -9 $javaid
