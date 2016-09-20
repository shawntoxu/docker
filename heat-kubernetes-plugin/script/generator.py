#!/usr/bin/python
import getopt
import json
import sys
import copy
import ConfigParser


def read_env(path):
    config = ConfigParser.ConfigParser()
    config.optionxform = str
    config.read(path)
    total_section = config.sections()
    env = list()
    for sSection in total_section:
        #print "Section = ", sSection
        for item in config.items(sSection):
            pair = dict()
            pair["name"] = item[0]
            pair["value"] = item[1]
            env.append(pair)
            #print "key = %s, valule = %s" % (item[0], item[1])
    #print "env list:%s" % env
    return env

def read_definition(path):
    file_obj = open(path)
    content = None
    try:
        content = file_obj.read()
    finally:
        file_obj.close()
    return content

def usage():
    print "-h, --help: Print usage message\n"
    print "-i, --input=: Specify the input json format file for the conversion\n"
    print "-o, --output=: Specify the generated output json file, default value is <input_file>.replaced\n"
    print "-p, --parallel=: Start components in parallel mode\n"
    print "--filter-walle-web: delete resources of walle-web RC and SVC\n"
    print "--split-walle-java: split wall-java replicas into individual RC and SVC\n"

def filter(ress):
    for res in FILTER_LIST:
        if res in ress:
            ress.pop(res)

def check_k8s_json(k8s_json):
    # replace all '_' with '-' and lower all the characters
    name = k8s_json['metadata']['name']
    name = name.replace('_', '-')
    name = name.lower()
    k8s_json['metadata']['name'] = name

def set_java_debug_port(resources):
    debug_port_list = range(9201, 9208)

    for key, val in resources.items():
        try:
            if val['properties']['definition']['kind'] != 'ReplicationController':
                continue
            for container_spec in  val['properties']['definition']['spec']['template']['spec']['containers']:
                env_list = container_spec['env']
                java_debug_enabled = False
                java_debug_env = None
                for env in env_list:
                    if env['name'] == 'ENABLE_JAVA_DEBUG':
                        java_debug_env = env
                        if env['value'] == 'Y':
                            java_debug_enabled = True
                            break

                if not java_debug_enabled:
                    if java_debug_env:
                        env_list.remove(java_debug_env)
                    remove_port_index_list = []
                    ports = container_spec['ports']
                    for i in range(len(ports)):
                        if ports[i]['containerPort'] in debug_port_list:
                            remove_port_index_list.append(i)
                    for index in remove_port_index_list:
                        ports.pop(index)
        except:
            pass

def main(argv):
    # read heat deployment json first
    # go though all resource defintion, read the json content from the given
    # path and load these content to embed into the resource defintion

    try:
        opts, args = getopt.getopt(argv, 'hi:o:p', ['help', 'input=', 'output=', 'parallel', 'filter-walle-web', 'split-walle-java'])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    output = None
    input = None
    no_dep = False
    filter_flag = False 
    split_flag = False

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-i', '--input'):
            input = arg
            if not output:
                output = arg + ".replaced"
        elif opt in ('-o', '--output'):
            output = arg
        elif opt in ('-p'):
            no_dep = True
        elif opt in ('--filter-walle-web'):
            filter_flag = True
        elif opt in ('--split-walle-java'):
            split_flag = True

    source = "".join(args)
    if not input:
        usage()
        exit(2)

    heat_content = read_definition(input)
    heat_json = json.loads(heat_content)
    resources = heat_json['resources']

    for key, val in resources.items():
        # load k8s json first
        path = val['properties']['definition_location']
        content = read_definition(path)

        try:
            k8s_json = json.loads(content)
        except:
            print "failed to load json file <%s>" % (path)
            exit(1)

        check_k8s_json(k8s_json)

        if val['type'] == 'GoogleInc::Kubernetes::ReplicationController': 
            env_path = k8s_json['spec']['template']['spec']['containers'][0]['env']

            if not isinstance(env_path, list):
                #print "env_path:%s" % env_path
                env_raw = read_env(env_path)
                k8s_json['spec']['template']['spec']['containers'][0]['env'] = env_raw

        if no_dep:
            # remove 'depends_on'
            heat_json['resources'][key].pop('depends_on', None)

        if filter_flag and 'depends_on' in val:
            heat_json['resources'][key]['depends_on'] = list(
                set(heat_json['resources'][key]['depends_on']) - set(FILTER_LIST))

        heat_json['resources'][key]['properties'].pop('definition_location', None)
        heat_json['resources'][key]['properties']['definition']=k8s_json

    if filter_flag:
        filter(heat_json['resources'])

    if split_flag:
        split_walle_java(heat_json['resources'])

    set_java_debug_port(heat_json['resources'])

    # dump the generated json
    with open(output, 'w') as outfile:
        json.dump(heat_json, outfile, sort_keys = True, indent = 4,
                  ensure_ascii=False)

if __name__ == '__main__':
    main(sys.argv[1:])
