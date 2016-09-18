FROM abc:5000/paas/u14-ssh-jdk1.8:1.0

ADD  ./server-1.0-SNAPSHOT.jar  /root/app/server-1.0-SNAPSHOT.jar
ADD ./start.sh /root/start.sh
ADD ./stop.sh /root/stop.sh 

EXPOSE 41000 41001

CMD ["/bin/sh","-c","/root/start.sh"]



