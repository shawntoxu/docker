#!/bin/bash

CATALINA_HOME=/root/app/tomcat/
#change log dir
IP=`ifconfig eth0 | grep "inet addr" | awk  '{print $2}' | awk -F ":" '{print $2}'`
mkdir ${CATALINA_HOME}/logs/$IP
sed -i s/logs/logs\\\/$IP/g  ${CATALINA_HOME}/conf/logging.properties
sed -i s/catalina.out/$IP\\\/catalina.out/g ${CATALINA_HOME}/bin/catalina.sh
sed -i s/logs/logs\\\/$IP/g ${CATALINA_HOME}/conf/server.xml

#restart nginx 
service nginx restart 
# start tomcat
echo "`date`:start tomcat begin">>/tmp/tomcat.log
bash ${CATALINA_HOME}/bin/startup.sh >>/tmp/tomcat.log
echo "`date`:start tomcat over">>/tmp/tomcat.log
# start ssh
/usr/sbin/sshd -D

