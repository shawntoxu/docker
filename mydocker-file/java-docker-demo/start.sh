#!/bin/bash 
#change log dir
#IP=`ifconfig eth0 | grep "inet addr" | awk  '{print $2}' | awk -F ":" '{print $2}'`
#logdir=/mnt/$IP
#mkdir /mnt/$IP
#ln $logdir -s /root/log/
# start java
#java ${JAVA_OPTS} -jar /root/app/server-1.0-SNAPSHOT.jar &
java  ${JAVA_OPTS} -server -Xms1g -Xmx1g  -Xmn512m -XX:PermSize=64m -XX:MaxPermSize=128m -XX:+UseConcMarkSweepGC -XX:+UseCMSCompactAtFullCollection -XX:CMSInitiatingOccupancyFraction=70 -XX:+CMSParallelRemarkEnabled -XX:SoftRefLRUPolicyMSPerMB=0 -XX:+CMSClassUnloadingEnabled -XX:SurvivorRatio=8 -XX:+DisableExplicitGC -verbose:gc -Xloggc:/root/log/gc.log -XX:+PrintGCDetails -jar /root/app/server-1.0-SNAPSHOT.jar &
# start ssh
/usr/sbin/sshd -D
