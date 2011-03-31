#!/bin/bash

if [ ! -d $(pwd)/coverage ]; then
  mkdir -p $(pwd)/coverage
fi

VIRT_STATS_FILE="$(pwd)/coverage/libvirt_API_statistics.txt"
PYTHON="python$(python -V 2>&1|cut -c 8-10)"
SUMMARY="coverage/coverage.txt"

if [ $(uname -p) = "x86_64" ]; then
  export LIB="lib64"
else
  export LIB="lib"
fi

function delimiter()
{
    local i=1
    local separator=$1
    local line=''
    while [ $i -le $2 ]
    do
        line=${line}${separator}
        i=$((i+1))
    done
    echo "+$line+" | tee -a $SUMMARY
}

echo
echo "Generate Libvirt API Statistics Report under the "
echo "$(pwd)/coverage" 
echo
delimiter '=' 50
echo -e "|	Libvirt API statistics of coverage\t   |" | tee -a $SUMMARY
echo -e "|	  $(date +'%F %T') ($(whoami))\t\t   |" | tee -a $SUMMARY
delimiter '=' 50

VIRT_PATH="/usr/$LIB/$PYTHON/site-packages/libvirt.py"
grep 'def ' $VIRT_PATH|grep -v "#"|grep -v "__init__" |grep -v "__del__"|cut -d"(" -f 1 |awk '{print NR, $2}' > $VIRT_STATS_FILE

TOTAL_API_NUM=$(grep 'def ' $VIRT_PATH|grep -v "#"|grep -v "__init__" |grep -v "__del__"|wc -l)
WRAPPER_API_PATH="$(pwd)/lib/Python"
WRAPPER_API_NUM=0

for wrapper in connect domain network storage nodedev interface secret nwfilter
do
  export EVERY_API_NUM=$(grep 'def ' $WRAPPER_API_PATH/$wrapper'API.py'|grep -v '#'|grep -v '__init__' |grep -v '__del__r'|wc -l)
  API_NUM=${EVERY_API_NUM}
  let WRAPPER_API_NUM=$WRAPPER_API_NUM+$API_NUM
  echo -e "| cover $wrapper API number\t|\t$API_NUM\t   |" | tee -a $SUMMARY
  if [ $wrapper != "nwfilter" ]; then
    delimiter '-' 50
  else
    continue
  fi 
done

delimiter '=' 50
echo -e "| cover libvirt API total number|\t$WRAPPER_API_NUM\t   |" | tee -a $SUMMARY
delimiter '-' 50

echo -e "| libvirt API real total number\t|\t$TOTAL_API_NUM\t   |" | tee -a $SUMMARY
delimiter '=' 50

RATE=$(printf "%.0f%%" `echo "scale=2;$WRAPPER_API_NUM/$TOTAL_API_NUM*100"|bc`)
echo -e "| libvirt API coverage rate\t|\t$RATE\t   |" | tee -a $SUMMARY
delimiter '=' 50

echo | tee -a $SUMMARY


