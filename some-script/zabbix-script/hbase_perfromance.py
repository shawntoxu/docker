
#!/usr/bin/env python
#coding=utf-8
import datetime
import getopt
import json
import math
import os
import sys
import time
import urllib2
import linecache

'''
Created on 2015年9月15日
@author: shawn.wang

出现以下情况打印ERROR 
backupMasterSize 小于 1 
deadServer 中有值,即[]不为空

出现以下情况打印 WARN 
clusterRequest 大于8000
nodeRequest中 每个Key对应的value值大于2000 
'''
ZAB_WARN    = "ZAB_WARN"
ZAB_ERROR   = "ZAB_ERROR"
ZAB_OK      = "ZAB_OK"

HBASEMONITOR_LOG   = "/etc/zabbix/scripts/log/HBaseMonitor.log"
#定义几个阈值
BACKUP_MASTER_SIZE = 1  
CLUSTE_RREQUEST_NUM    = 8000
NODE_REQUEST_NUM       = 2000 

#LAST_TIME =""

def usage():
    print sys.argv[0], "HBaseMonitorlogpath  BACKUP_MASTER_SIZE  CLUSTE_RREQUEST_NUM  NODE_REQUEST_NUM"
    print "\tpython vncc_hbase_performance.py /etc/zabbix/scripts/log/HBaseMonitor.log 1 8000 2000"
    exit()


def exit_print(rank, msg):
    OUTPUT_FORMAT = "[%s]%s"
    print OUTPUT_FORMAT % (rank, msg)
    exit()
    

def get_lastline(filepath):
    #file=open('/etc/zabbix/scripts/log/HBaseMonitor.log','r')
    tgfile=open(filepath,'r')
    linecount=len(tgfile.readlines())
    lastline = linecache.getline(filepath,linecount)
    #取得上次时间 和 log内容
    return lastline[:20].strip(),lastline[20:].strip()

def hbaselog_check():
   # while True:
        thistime,lastlog = get_lastline(HBASEMONITOR_LOG)
        #print thistime,lastlog
        currenttime = datetime.datetime.now()
        logtime = datetime.datetime.strptime(thistime, "%Y-%m-%d %H:%M:%S")
        timeover = currenttime - logtime 
        #时间差小于20秒
        if timeover < datetime.timedelta(seconds=20):
            do(lastlog)
        else:
           exit_print(ZAB_ERROR,"HBse log file timeout!")
    
def do(log):
    jsonobj = json.loads(log)

    bkmastersize = jsonobj.get("backupMasterSize")
    deadserver = jsonobj.get("deadServer")
    
    
    if bkmastersize < BACKUP_MASTER_SIZE:
        exit_print(ZAB_ERROR,"BACKUP_MASTER_SIZE < %s" %BACKUP_MASTER_SIZE)
        
    if len(deadserver) >= 1 :
        exit_print(ZAB_ERROR,"deadServer  is not null , %s" %deadserver)
        
    clusterRequest  = jsonobj.get("clusterRequest")
    
    if clusterRequest > CLUSTE_RREQUEST_NUM:
        exit_print(ZAB_WARN,"CLUSTE_RREQUEST_NUM(%d) > %s"%(clusterRequest,CLUSTE_RREQUEST_NUM))

    nodeRequest = jsonobj.get("nodeRequest")
    
    i=0
    total=len(nodeRequest)
    for k,v in nodeRequest.items():
        if v < NODE_REQUEST_NUM:
            #print "print ok"
            break
        else:
            i=i+1
    if i==total:
        exit_print(ZAB_WARN,"NODE_REQUEST_NUM > %s" %NODE_REQUEST_NUM)

    #一切阈值都未超出预期 打印ok
    exit_print(ZAB_OK,"Successful")


if __name__ == '__main__':
    if len(sys.argv) != 5:
        usage()
    else:
        HBASEMONITOR_LOG = sys.argv[1]
        BACKUP_MASTER_SIZE= int(sys.argv[2])
        CLUSTE_RREQUEST_NUM = int(sys.argv[3])
        NODE_REQUEST_NUM = int(sys.argv[4])
    hbaselog_check()
