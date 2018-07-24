#remove docker
apt-get remove docker-ce 
 
dpkg --list | grep docker 
dpkg --purge  docker-ce 
