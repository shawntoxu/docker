#! /bin/bash
#log check

export PATH=/sbin:/usr/sbin:/usr/local/sbin:/usr/local/bin:/usr/bin:/bin

if [ -f ~/.bashrc ]; then
      . ~/.bashrc
fi

usage()
{
    echo "$0 <log_path> <max_log_count> <max_log_size_in_MBytes>"
    echo "e.g. $0 /var/log/etcd/etcd.log 7"
}

if [[ $# != 3 ]]; then
    usage && exit
fi

log_file=$1
max_file=$2
let max_file_size_bytes=$3*1024*1024

exec 6>&1 1>>/var/log/paas/paas.log 2>&1

if [ $max_file -lt 2 ]; then
    echo "log count too small!"
    usage && exit
fi

if [ ! -f "$log_file" ]; then
    echo "log file " $log_file " does not exist!"
    usage && exit
fi

size_in_bytes=`stat -c %s $log_file`
if [ $size_in_bytes -ge $max_file_size_bytes ];
then
    new_log_file="$log_file-`date '+%Y-%m-%d-%H:%M:%S'`"
    echo "create new file:" $new_log_file
    cp $log_file $new_log_file
    echo > $log_file
fi

size=`ls $log_file-* | wc -l`
if [ $size -ge $max_file ];
then
    echo "remove file" `ls -tl $log_file-* | tail -1 | awk '{printf$9}'`
    rm `ls -tl $log_file-* | tail -1 | awk '{printf$9}'`
fi

