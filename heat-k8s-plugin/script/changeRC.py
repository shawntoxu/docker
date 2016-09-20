#!/usr/bin/python
#coding=utf-8
import json
import sys
import random
'''
@author: shawn.wang
change internalID to internalID+raddomnum
change rcname to rcname+internalID
'''
def read_definition(heat_json_path):
    file_obj = open(heat_json_path)
    content = None
    try:
        content = file_obj.read()
    finally:
        file_obj.close()
    return content
    
    
def changeRcNameAndinternalID(jsonfile,rcnamelist):
    content=read_definition(jsonfile)
    rs=json.loads(content)
    resources = rs['resources']
    raddomnum=random.randrange(0, 1000)
    for key, val in resources.items():
      #filter all rc name
        if "svc" not in key:
            rcname=val['properties']['definition']['metadata']['name']
            rclabelname=val['properties']['definition']['metadata']['labels']['name']
	    if rclabelname in rcnamelist:
		internalID=val['properties']['definition']['metadata']['labels']['internalID']
                #raddomnum=random.randrange(0, 10000)
                new_internalID=int(internalID)+raddomnum
                rs['resources'][key]['properties']['definition']['metadata']['name'] = rcname+"-"+str(new_internalID)
                #set internalID
                rs['resources'][key]['properties']['definition']['metadata']['labels']['internalID']=str(new_internalID)
                rs['resources'][key]['properties']['definition']['spec']['selector']['internalID']=str(new_internalID)
                rs['resources'][key]['properties']['definition']['spec']['template']['metadata']['labels']['internalID']=str(new_internalID)
    with open(jsonfile, 'w') as outfile:
        json.dump(rs, outfile, sort_keys = True, indent = 4,
                  ensure_ascii=False)
                    
if __name__ == '__main__':
    arglist=sys.argv[1:]
    jsonfile=arglist[0]
    rcnamelist=arglist[1:]
    newrcnamelist=[]
    for rc in rcnamelist:
        rc=rc.replace('_', '-')
        newrcnamelist.append(rc) 
    changeRcNameAndinternalID(jsonfile,newrcnamelist)

