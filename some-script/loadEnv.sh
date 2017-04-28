#!/bin/bash 
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo $DIR 

#加载配置中的环境变量
. $DIR/test.conf
echo $MY_ENV 
export MY_ENV

export PATH=$MY_ENV:$PATH 
