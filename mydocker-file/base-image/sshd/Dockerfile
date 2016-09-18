FROM abc:5000/ubuntu:14.04
MAINTAINER shanw
RUN apt-get install -y openssh-server

RUN mkdir -p /var/run/sshd

RUN sed -i 's/^PermitRootLogin/#PermitRootLogin/' /etc/ssh/sshd_config  
RUN echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
RUN sed -i 's/UsePAM yes/UsePAM no/g' /etc/ssh/sshd_config

RUN echo "root:000000" | chpasswd
EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
