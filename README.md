# ez_port_forward
[![PyPI - Version](https://img.shields.io/pypi/v/ez-port-forward?style=flat-square&logo=pypi&label=PyPI)](https://pypi.org/project/ez-port-forward/) [![PyPI - Downloads](https://img.shields.io/pypi/dm/ez-port-forward?style=flat-square&logo=pypi)](https://pypi.org/project/ez-port-forward/) [![github](https://img.shields.io/badge/GitHub-100000?style=flat-square&logo=github&logoColor=white)](https://github.com/rk-exxec/ez_port_forward) 


Create DNAT port forwarding rules from easy-to-read YAML files.

Are you tired of always having to look up the `iptables` command every couple of months to change a single port forwarding on your proxmox/hypervisor because a friend asks you to make a new container for that very popular new game?

Here is the solution:   
A YAML-powered port forwarding tool, that does all that for you. 
You simply need to change some numbers in the very readable and easy-to-understand config file. The script then converts that to 100% valid `iptables` commands.

Has shortcut notation for multiple ports and ssh ports, and can do different input and output ports.  
Checks port collisions and validity.



## Installation:
`pip install ez_port_forward`

Installs a command `ez-port-forward` and its shorthand `ezpf`.

## Usage:

- `ez-port-forward`:  
Looks in the current dir for a file named `port_config.yaml` and writes the results to `/etc/network/interfaces.d/port_forwards`.  
WILL REPLACE THE FILE WITHOUT ASKING!  

- `ez-port-forward /path/to/my/port_config.yaml`:  
Uses given input file and writes results to `/etc/network/interfaces.d/port_forwards`.  
WILL REPLACE FILE WITHOUT ASKING!  

- `ez-port-forward -o /target/path/port_forwards`:  
Looks in the current dir for a file named `port_config.yaml` and writes the results to the given output file.  
WILL REPLACE THE FILE WITHOUT ASKING!  

- `ez-port-forward /path/to/my/port_config.yaml -o /target/path/port_forwards`:  
Uses the given input file and writes the results to the given output file.  
WILL REPLACE THE FILE WITHOUT ASKING!  

Same usage for the `ezpf` shorthand.

## Requirements:

Python >= 3.9  
PyYAML

Make sure your `/etc/network/interfaces` config contains the line
`source /etc/network/interfaces.d/*`.

Tested on Proxmox.

## Example:

```yaml
# the name of the bridge
vmbr0:
    # the interface the bridge is connected to
    bridge: eno1
    # the ip range of your subnet you want to make port forwards in
    # container ID are used as last octet for the ip
    subnet: 10.0.0.0/24
    # this section contains all the forwarding magic
    forwards: 
    # this forwards to the container with id 101 and ip 10.0.0.101
        101:
            # forwards external port 10122 to internal port 22
            ssh: true
            # forwards multiple external ports to identical internal ports for tcp udp and both
            tcp: 123,345,567
            udp: 888,999
            tcpudp: 111,222
        102: 
            # maps external ports 321,345,765 to internal ports 123,345,567
            tcp: 
                321: 123
                345: 345 # will notice this port collision with 101 and mark the line in the output as comment
                765: 567
        201: # this is equivalent to below
            ssh:
        202:
            tcp:
                20222: 22
        233:
            # use port 23 for ssh shorthand, forwards 23323 to 23
            ssh: 23 
```

Result:
```bash
iface vmbr0 inet static
#--- Container 101
        post-up iptables -t nat -A PREROUTING -i eno1 -p tcp --dport 10122 -j DNAT --to 10.0.0.101:22
        post-up iptables -t nat -A PREROUTING -i eno1 -p tcp --dport 123 -j DNAT --to 10.0.0.101:123
        post-up iptables -t nat -A PREROUTING -i eno1 -p tcp --dport 345 -j DNAT --to 10.0.0.101:345
        post-up iptables -t nat -A PREROUTING -i eno1 -p tcp --dport 567 -j DNAT --to 10.0.0.101:567
        post-up iptables -t nat -A PREROUTING -i eno1 -p udp --dport 888 -j DNAT --to 10.0.0.101:888
        post-up iptables -t nat -A PREROUTING -i eno1 -p udp --dport 999 -j DNAT --to 10.0.0.101:999
        post-up iptables -t nat -A PREROUTING -i eno1 -p tcp --dport 111 -j DNAT --to 10.0.0.101:111
        post-up iptables -t nat -A PREROUTING -i eno1 -p udp --dport 111 -j DNAT --to 10.0.0.101:111
        post-up iptables -t nat -A PREROUTING -i eno1 -p tcp --dport 222 -j DNAT --to 10.0.0.101:222
        post-up iptables -t nat -A PREROUTING -i eno1 -p udp --dport 222 -j DNAT --to 10.0.0.101:222
#---
#--- Container 102
        post-up iptables -t nat -A PREROUTING -i eno1 -p tcp --dport 321 -j DNAT --to 10.0.0.102:123
#        post-up iptables -t nat -A PREROUTING -i eno1 -p tcp --dport 345 -j DNAT --to 10.0.0.102:345
        post-up iptables -t nat -A PREROUTING -i eno1 -p tcp --dport 765 -j DNAT --to 10.0.0.102:567
#---
#--- Container 201
        post-up iptables -t nat -A PREROUTING -i eno1 -p tcp --dport 20122 -j DNAT --to 10.0.0.201:22
#---
#--- Container 202
        post-up iptables -t nat -A PREROUTING -i eno1 -p tcp --dport 20222 -j DNAT --to 10.0.0.202:22
#---
#--- Container 233
        post-up iptables -t nat -A PREROUTING -i eno1 -p tcp --dport 23323 -j DNAT --to 10.0.0.233:23
#---
```
