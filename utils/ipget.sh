#!/bin/sh

mac=$1
if [[ -z $mac ]]; then
   echo "mac address is null."
   exit 1
fi

if ! type nmap >/dev/null 2>&1; then
   echo "nmap package needs to be installed."
   exit 1
fi

ipaddr=`ip route |grep virbr0 |sed -n 1p|awk {'print $1'}`

#if lsmod | grep kvm > /dev/null ;then
#  ipaddr=`ip route |grep switch |sed -n 1p|awk {'print $1'}`
#fi

if [[ -n $ipaddr ]]; then
   output=$(nmap -sP -n $ipaddr|grep -i -B 2 $mac)
   if [[ -n $output ]]; then
      hostip=$(echo $output | sed -e 's/.* \([0-9]*\.[0-9]*\.[0-9]*\.[0-9]*\).*/\1/')
   fi
fi
echo $hostip
