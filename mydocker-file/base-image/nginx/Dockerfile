FROM abc:5000/paas/u14-ssh-jdk1.8:1.0
bc/g

MAINTAINER paas/shawn

RUN \ 
     apt-get update && apt-get install -y python-software-properties  software-properties-common \
     && add-apt-repository ppa:nginx/stable \
     && apt-get update \
     && apt-get install -y  nginx \
     && rm -rf /var/lib/apt/lists/* 

EXPOSE 80 22

CMD service nginx start; /usr/sbin/sshd -D



