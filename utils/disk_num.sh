#!/bin/sh

guestname=$1
if [[ -z $guestname ]]; then
    echo "need guestname as the parameter."
    exit 1
fi

virsh dumpxml $guestname > guestdump.xml
if [ -f guestdump.xml ]; then
   num=$(grep "</disk>" guestdump.xml | wc -l )
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
    
  

