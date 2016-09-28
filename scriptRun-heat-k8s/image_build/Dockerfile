FROM abc:5000/gkt/gkt-jdk1.8-tomcat8:1.0

ADD ./app/ROOT /root/app/tomcat/webapps/ROOT
ADD ./start.sh /root/start.sh
#ADD ./run_once.sh /root/run_once.sh
RUN mkdir /root/shell/lib -p 
#ADD ./lib/* /root/shell/lib/
#ADD ./cron/*.sh /root/shell/

EXPOSE 8080 22
CMD ["/bin/sh","-c","/root/start.sh"]

