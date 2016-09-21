#coding=utf-8
import json
import sys
import urllib2
import string
import time
import datetime
import os

'''
@author: shawn.wang
删除docker 中的指定namespace下 ，指定时间以前创建的 image
注：采用docke remote api 查询image，docker 需要以TCP模式运行
'''
# before 2016-06-18 delete  
before_time=1466179200

docker_hub_ip='172.30.80.33'
docker_hub_port='2375'

def get_delete_iamges(namespace='test_namespace',before_time=None):
    req = urllib2.Request('http://{}:{}/images/json'.format('172.30.80.33','2375'))
    response = urllib2.urlopen(req)
    recv_json = json.load(response)
    #print recv_json
    for item in recv_json:
        #print item['RepoTags']
        imagelist=item['RepoTags']
        for image in imagelist:
            if image.find(namespace) != -1:
                if ( before_time - item['Created'] ) > 0 :
                    #print item['Created']
                    print 'delete image  create time=' + str(item['Created'])
                    # call docker rmi -f xxx 
                    os.system('docker rmi -f ' + image)
                    print image

def get_current_time():
    timestr=str(time.time())
    times=string.split(timestr,'.')
    return times[0]

if __name__ == '__main__':
    #get_delete_iamges('test',before_time)
    get_delete_iamges('myspace',before_time)
    #time.strftime('1466179200','%Y-%m-%d %H:%M:%S')
    #pass
