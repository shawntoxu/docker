FROM node:argon
#FROM node:4.5.0

MAINTAINER  PaaS/Shawn


RUN apt-get update && apt-get install -y openssh-server &&  rm -rf /var/lib/apt/lists/* 
RUN mkdir -p /var/run/sshd

RUN sed -i 's/^PermitRootLogin/#PermitRootLogin/' /etc/ssh/sshd_config  
RUN echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
RUN sed -i 's/UsePAM yes/UsePAM no/g' /etc/ssh/sshd_config

RUN echo "root:Letmein123" | chpasswd

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]

