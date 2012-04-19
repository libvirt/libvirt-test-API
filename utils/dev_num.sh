#!/bin/sh
# counting disk and interface numbers

guestname=$1
device=$2
if [[ -z $guestname ]] || [[ -z $device ]]; then
    echo "need guestname and device element as the parameter."
    exit 1
fi

virsh dumpxml $guestname > guestdump.xml
if [ -f guestdump.xml ]; then
   num=$(grep "</$device>" guestdump.xml | wc -l )
   if [[ -z $num ]]; then
       echo "no disk in the domain, can you image that? "
       rm -f guestdump.xml
   else
       echo $num
       rm -f guestdump.xml
   fi
else
   echo "failed to dump the xml description of the domain $guestname."
   rm -f guestdump.xml
   exit 1
fi
