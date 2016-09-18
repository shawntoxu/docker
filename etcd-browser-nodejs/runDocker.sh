#sudo docker build -t etcd-browser .
sudo docker run --rm --name etcd-browser -p 0.0.0.0:8080:8000 --env ETCD_HOST=10.2.33.10 --env AUTH_PASS=doe -t -i local/etcd-browser
