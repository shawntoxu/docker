import psutil
import sys
import re

IPs_str= sys.argv[1]
IP_list = re.split(' *', IPs_str)

ifs = psutil.net_if_addrs()
for key, value in ifs.items():
    for elem in value:
        if elem.address in IP_list:
            print elem.address
            sys.exit(0)

sys.exit(1)
