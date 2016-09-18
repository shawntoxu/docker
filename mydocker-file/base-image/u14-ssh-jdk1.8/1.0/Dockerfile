FROM abc:5000/paas/ubuntu-sshd
MAINTAINER shawntoxu

# Default to UTF-8 file.encoding
ENV LANG C.UTF-8

RUN apt-get update && apt-get install -y software-properties-common python-software-properties
RUN add-apt-repository -y ppa:webupd8team/java
RUN echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections
RUN apt-get update && apt-get install -y oracle-java8-installer oracle-java8-set-default

RUN locale-gen en_US.UTF-8
EXPOSE 22

CMD /usr/sbin/sshd -D
