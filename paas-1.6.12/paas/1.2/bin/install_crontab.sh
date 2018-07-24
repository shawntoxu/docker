#!/bin/bash

mkdir /tmp/paas 2>&1>/dev/null

crontab_file="/tmp/paas/crontab"

crontab -l > $crontab_file

# delete old lines
sed -i "/docker_container_clean.sh/d" $crontab_file
sed -i "/paas_arrange_log.sh/d" $crontab_file
sed -i "/docker_image_clean.sh/d" $crontab_file
sed -i "/ipcleaner.sh/d" $crontab_file
sed -i "/\/opt\/paas/d" $crontab_file

# install new crontab
cat $PAAS_CONFDIR/crontab >> $crontab_file
crontab -u root $crontab_file

