import os, sys
from pathlib import Path
import yaml

with open("port_conf.yaml") as conf:
    port_conf_dict : dict = yaml.load(conf)

with open("port_forwards", "w") as output:

    for iname,iconf in port_conf_dict.items():
        output.write(f"iface {iname} inet static")
        bridge = iconf.pop("bridge")

        for cont_id, cont_conf in iconf.items():
            ssh = cont_conf.pop("ssh", False)
            tcp = cont_conf.pop("tcp", None)
            udp = cont_conf.pop("udp", None)
            tcpudp = cont_conf.pop("tcpudp", None)

            

def parse_protocols(prot_obj):
    if not prot_obj: return None
    if  isinstance(prot_obj, str):
        ports = {int(x.strip()):int(x.strip()) for x in prot_obj.split(",")}
    elif isinstance(prot_obj, dict):
        ports = {int(k):int(v) for k,v in prot_obj.items()}
    else: 
        return None



    