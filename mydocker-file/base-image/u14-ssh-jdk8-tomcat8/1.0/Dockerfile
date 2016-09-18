FROM abc:5000/paas/u14-ssh-jdk1.8:1.0
bc/g

MAINTAINER PaaS/shawn

RUN mkdir /root/app/tomcat -p

RUN apt-get install unzip -y

ADD ./apache-tomcat-8.0.30 /root/app/tomcat

#Define commonly used JAVA_HOME variable
#ENV JAVA_HOME /usr/lib/jvm/java-8-oracle

EXPOSE 22

CMD /usr/sbin/sshd -D


