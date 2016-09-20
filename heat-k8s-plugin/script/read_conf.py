#!/usr/bin/env python

import json
import getopt
import sys
import copy

class ResourceRC:
    def __init__(self, name, json_data):
        self.json_data = copy.deepcopy(json_data)
        self.name = name

        # In heat.json file, the term "service" is used. However in CD
        # part, the term "services" is used for the name of component
        # tar files and the name of docker images. So create a name map
        # for short-term soluion.
        self.name_map = {
            "rulescript-service" : "rulescript-services",
            "mq-service" : "mq-services",
            "rdb-service" : "rdb-services",
            "fbagent-service" : "fbagent-services",
            "data-service" : "data-services",
        }

    def get_name(self):
        return self.name

    def get_component_name(self):
        name = self.json_data['properties']['definition']['metadata']['labels']['name']

        # replace walle-java-n with walle-java
        if name.find('walle-java') == 0:
            name = 'walle-java'

        if name in self.name_map:
            name = self.name_map[name]
        return name

    def check_consistency(self):
        version_str1 = self.json_data['properties']['definition']['metadata']['labels']['version']
        version_str2 = self.json_data['properties']['definition']['spec']['selector']['version']
        version_str3 = self.json_data['properties']['definition']['spec']['template']['metadata']['labels']['version']
        if (version_str1 != version_str2) or (version_str1 != version_str3) or (version_str2 != version_str3):
            print "ERROR: [%s] different version strings are specified in the file" % self.name
            return False

        image = self.json_data['properties']['definition']['spec']['template']['spec']['containers'][0]['image']
        image_tag = image.split(':')[-1]
        if image_tag != version_str1:
            print "ERROR: [%s] image tag <%s> is not correct" % (image_tag, self.name)
            return False

        return True

    def get_version(self):
        return self.json_data['properties']['definition']['metadata']['labels']['version']


def read_definition(path):
    content = None
    file_obj = None
    try:
        file_obj = open(path)
        content = file_obj.read()
    except Exception, e:
        print e
    finally:
        if file_obj != None:
            file_obj.close()
    return content

def usage():
    print "Usage: %s [options] heat_json_file" % sys.argv[0]
    print "    -h, --help: Print usage message"
    print "    -w, --wide: Print each column in wide mode"

def main(argv):
    # read heat deployment json first
    # go though all resource defintion, read the json content from the given
    # path and load these content to embed into the resource defintion

    dsp_wide_mode = False

    try:
        opts, args = getopt.getopt(argv, 'hw', ['help', 'wide'])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-v', '--components-version'):
            pass
        elif opt in ('-w', '--wide'):
            dsp_wide_mode = True

    if len(args) != 1:
        print "ERROR: Please specify one heat.json file"
        usage()
        sys.exit()

    content = read_definition(args[0])
    if content == None:
        sys.exit()

    heat_json = json.loads(content)
    resource_dict = heat_json['resources']
    
    rc_list = []
    rc_dict = {}
    for key, val in resource_dict.items():
        if val['properties']['definition']['kind'] != 'ReplicationController':
            continue
        rc = ResourceRC(key, val)
        if not rc.check_consistency():
            sys.exit(1)

        if not rc.get_component_name() in rc_dict:
            rc_dict[rc.get_component_name()] = rc
            rc_list.append(rc)

    for rc in rc_list:
        if dsp_wide_mode:
            print "%s %s" % (rc.get_component_name(), rc.get_version())
        else:
            print "%-35s%s" % (rc.get_component_name(), rc.get_version())

if __name__ == "__main__":
    main(sys.argv[1:])

