#coding=utf-8
import json
import sys
'''
@author: shawn.wang
get last time josnfile internalID
'''
JSONFILE=''
OLDJSONFILE=''

def read_definition(heat_json_path):
    file_obj = open(heat_json_path)
    content = None
    try:
        content = file_obj.read()
    finally:
        file_obj.close()
    return content

def read_internalID(last_jsonfile):
    if last_jsonfile == "@":
        return None
    content=read_definition(last_jsonfile)
    rs=json.loads(content)
    resources = rs['resources']
    idmap = {} 
    for key, val in resources.items():
        if "svc" not in key:
            rclabelname=val['properties']['definition']['metadata']['labels']['name']
            internalID=val['properties']['definition']['metadata']['labels']['internalID']
            #internalID=val['properties']['definition']['metadata']['labels']['internalID']
            idmap.setdefault(rclabelname,internalID)
    return idmap
    
def changeRcNameAndinternalID(jsonfile,rcnamelist,idmap):
    content=read_definition(jsonfile)
    rs=json.loads(content)
    resources = rs['resources']
    for key, val in resources.items():
        if "svc" not in key:
            rclabelname=val['properties']['definition']['metadata']['labels']['name']
	    rcname=val['properties']['definition']['metadata']['name']
            if idmap.has_key(rclabelname):
                old_internalID = int(idmap[rclabelname])
		rs['resources'][key]['properties']['definition']['metadata']['name'] = rcname+"-"+str(old_internalID)
                #set internalID
                rs['resources'][key]['properties']['definition']['metadata']['labels']['internalID']=str(old_internalID)
                rs['resources'][key]['properties']['definition']['spec']['selector']['internalID']=str(old_internalID)
                rs['resources'][key]['properties']['definition']['spec']['template']['metadata']['labels']['internalID']=str(old_internalID)
    with open(jsonfile, 'w') as outfile:
        json.dump(rs, outfile, sort_keys = True, indent = 4,
                  ensure_ascii=False)

if __name__ == '__main__':
    #idmap=read_internalID(OLDJSONFILE)
    #arg1=generator json  arg2=last time json
    arglist=sys.argv[1:]
    if len(arglist) < 2:
	print "args:newjson lastjson"
        sys.exit(0) 
    idmap=read_internalID(arglist[1])
    if idmap is None:
	print "no lastjson,create"
        sys.exit(0)
    #for k,v in idmap.items():
    #    print k+"="+v
    rcnamelist=idmap.keys()
    changeRcNameAndinternalID(arglist[0],rcnamelist,idmap)
        
