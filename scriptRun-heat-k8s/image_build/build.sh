#!/bin/bash 
#bulid image & push to registry 
#push registry : dev aws ali 
#set -x 
usage(){
        echo "$0 push2address image_url"
        echo "e.g. $0 dev gkt/gkt-content-web:1.0"
}

if [ $# != 2 ]; then
      usage && exit
fi

push2address=$1
image_url=$2
basedir=$( cd ` dirname $0 ` && pwd )

dev_registry=dev.abc:5000
aws_registry=online.abc:5000
ali_registry=other.abc:5000
#if [ ! -d "$basedir/$1" ];then
#    #mkdir $ddir/web-images/$1 
#    echo "$basedir/$1 not found."
#    exit 1 
#fi

#targetdir=$basedir/$1/$3
#cp $basedir/Dockerfile $basedir/start.sh  $targetdir
#cp $basedir/run_once.sh  $targetdir

#change unzip app 
#unzip $targetdir/ROOT.war -d $targetdir/ROOT/

if [ "$push2address" = dev ];then
docker build -t $dev_registry/$image_url  $basedir
docker push  $dev_registry/$image_url
#rm -rf $targetdir/Dockerfile
#rm -rf $targetdir/start.sh
#rm -rf $targetdir/ROOT
fi

if [ "$push2address" = aws ];then
echo "------------------push to online-----------------------"
docker bulid $ali_registry/$image_url  $aws_registry/$image_url
docker push $ali_registry/$image_url
fi


if [ "$push2address" = aws ];then
echo "------------------push to online-----------------------"
docker build $aws_registry/$image_url  $aws_registry/$image_url
docker push $aws_registry/$image_url
fi 


