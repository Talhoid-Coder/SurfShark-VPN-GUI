#!/bin/bash
ip rule add from $(ifconfig eth0 | grep -oP "\binet\s+\K\S+" --color=never) table 128
ip route add table 128 to $(whois $(ifconfig eth0 | grep -oP "\binet\s+\K\S+" --color=never) | grep -oP "\bCIDR:\s+\K\S+" --color=never) dev eth0
ip route add table 128 default via $(ip route show | grep -oP "\bdefault via\s+\K\S+" --color=never)
