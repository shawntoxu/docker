#!/bin/bash
#set dbproperties
CATALINA_HOME=/root/app/tomcat
#unzip ${CATALINA_HOME}/webapps/ROOT.war -d ${CATALINA_HOME}/webapps/ROOT/
#sed -i s/#####/${DBCONFIG}/g  ${CATALINA_HOME}/webapps/ROOT/WEB-INF/classes/applicationContext.xml
#set tomcat memeory
sed -i '98aJAVA_OPTS="-server -Xms256m -Xmx512m "' ${CATALINA_HOME}/bin/catalina.sh

#change log dir
IP=`ifconfig eth0 | grep "inet addr" | awk  '{print $2}' | awk -F ":" '{print $2}'`
mkdir ${CATALINA_HOME}/logs/$IP
sed -i s/logs/logs\\\/$IP/g  ${CATALINA_HOME}/conf/logging.properties
sed -i s/catalina.out/$IP\\\/catalina.out/g ${CATALINA_HOME}/bin/catalina.sh
sed -i s/logs/logs\\\/$IP/g ${CATALINA_HOME}/conf/server.xml

# start tomcat
echo "`date`:start tomcat begin">>/tmp/tomcat.log
sh ${CATALINA_HOME}/bin/startup.sh >>/tmp/tomcat.log
echo "`date`:start tomcat over">>/tmp/tomcat.log
# start ssh
/usr/sbin/sshd -D

