# ez-port-forward makes it easier to create portforwarding rules via DNAT for proxmox systems or similar.
# Copyright (C) 2024  Raphael Kriegl

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


from io import TextIOWrapper
import os, sys
import argparse
from pathlib import Path

import yaml
from yaml import Loader

import ipaddress
import logging

# typing imports
from typing import TypeAlias, Union
from io import TextIOWrapper

PortMappingType: TypeAlias = Union[str,int,dict[int,int]]

# this dict keeps track of all ports opened
existing_port_maps: dict[tuple[int, str], ipaddress.IPv4Address] = dict()

def parse_protocols(prot_obj: PortMappingType):
    # returns dict that maps source ports to dest ports
    if not prot_obj: return None
    # bool is an invalid datatype, but would be accepted by the int check later
    if isinstance(prot_obj, bool): return None

    # if ports are given as comma separated list, it is read as text.
    # if only list is given, we assume identical source and dest ports
    if  isinstance(prot_obj, str) :
        return {int(x.strip()):int(x.strip()) for x in prot_obj.split(",")}
    # single ports are parsed as int
    elif isinstance(prot_obj, int):
        return {prot_obj:prot_obj}
    # yaml is read as dict, we only convert keys and values to ints
    elif isinstance(prot_obj, dict):
        return {int(k):int(v) for k,v in prot_obj.items()}
    # if yaml is incorrectly formatted, or entry is missing
    else: 
        return None


def build_command(protocol:str, bridge:str, target_ip:ipaddress.IPv4Address, target_port:int, source_port:int = None):
    if not source_port: source_port = target_port
    command = f"        post-up iptables -t nat -A PREROUTING -i {bridge} -p {protocol} --dport {source_port} -j DNAT --to {target_ip}:{target_port}\n"
    return command

def write_container_commands(file: TextIOWrapper, ip:ipaddress.IPv4Address, bridge:str, tcp_rules:PortMappingType=None, udp_rules:PortMappingType=None, tcpudp_rules:PortMappingType=None, ssh=None):

    def write_rules_helper(prot, src, dest):
        # if port number too large
        if(src > 65535 or dest > 65535):
            logging.warning(f"Port {src} or {dest} larger than max allowed (65535). Port forward will be commented out in the file.")
            file.write("#") # if the command is declared invalid it is still written to file, just commented out
        # if port was already opened
        if (src,prot) in existing_port_maps.keys():
            logging.warning(f"Port {src} already opened for {existing_port_maps[(src,prot)]}. Port forward will be commented out in the file.")
            file.write("#") # if the command is declared invalid it is still written to file, just commented out
        else:
            existing_port_maps[(src,prot)] = ip
        file.write(build_command(prot, bridge, ip, dest, src))

    if ssh: 
        write_rules_helper("tcp", *list(ssh.items())[0])

    if tcp_rules:
        for src, dest in tcp_rules.items():
            write_rules_helper("tcp", src, dest)

    if udp_rules:
        for src, dest in udp_rules.items():
            write_rules_helper("udp", src, dest)

    if tcpudp_rules:
        for src, dest in tcpudp_rules.items():
            write_rules_helper("tcp", src, dest)
            write_rules_helper("udp", src, dest)


def parse_yaml(yaml_file):
    with open(yaml_file) as conf:
        try:
            yaml_dict : dict = yaml.load(conf, Loader)
        except yaml.YAMLError as ye:
            logging.error(f"Error while parsing YAML file:  {str(ye)}")
            raise

    return yaml_dict

def write_iptables_file(yaml_dict, out_file):
    with open(out_file, "w") as output:

        for iname,iconf in yaml_dict.items():
            output.write(f"iface {iname} inet static\n")
            bridge = iconf.pop("bridge")
            subnet = ipaddress.IPv4Network(iconf.pop("subnet"))

            for cont_id, cont_conf in iconf["forwards"].items():
                output.write(f"#--- Container {cont_id}\n")
                try:
                    # this automatically creates an ip offset by the container id from base address in subnet and checks validity
                    container_ip = subnet[cont_id]

                    # check if ssh key in dict, and if it has a specified value
                    if "ssh" in cont_conf.keys():
                        ssh = cont_conf["ssh"]
                        if isinstance(ssh,bool) or not isinstance(ssh,int): 
                            ssh = {cont_id*100 + 22:22} # assign default if key exists and no int value is specified
                        else:
                            ssh = {cont_id*100 + ssh:ssh} # use specified internal ssh port if given

                    else: ssh = None
                            
                    tcp = parse_protocols(cont_conf.pop("tcp", None))
                    udp = parse_protocols(cont_conf.pop("udp", None))
                    tcpudp = parse_protocols(cont_conf.pop("tcpudp", None))
                                

                    write_container_commands(output, container_ip, bridge, tcp, udp, ssh, tcpudp)
                except Exception as ex:
                    logging.error(f"Error while parsing rules for Container ID {cont_id} for interface <{iname}> with subnet <{subnet}>: \n{ex}")
                    continue
                finally:       
                    output.write("#---\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_yaml", type=str, default="./port_conf.yaml", help="The input yaml file. Defaults to ./port_conf.yaml", nargs="?")
    parser.add_argument("-o", "--output", type=str, default="/etc/network/interfaces.d/port_forwards", help="Target path. Optional, defaults to /etc/network/interfaces.d/port_forwards", nargs="?")
    
    args = parser.parse_args()

    yaml_path = Path(args.input_yaml)
    out_path = Path(args.output)
    
    assert yaml_path.exists(), "Input file does not exist."
    # assert out_path, "Output path does not exist or is not writeable."

    yaml_dict = parse_yaml(yaml_path)

    write_iptables_file(yaml_dict, out_path)



if __name__ == "__main__":
    main()



    