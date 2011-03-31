#! /bin/sh
# Summary: create documentation of cases in Python
# Author: Osier Yang <jyang@redhat.com>
# Version: 0.1

FILES=`find $PWD/repos/Python -type f -name "*.py"`

for i in ${FILES}; do
    if [ `basename $i` != '__init__.py' ]; then
        DIRNAME=`dirname $i`
        DIRNAME=$(echo $DIRNAME | sed -e 's:repos:doc:g')
    fi

    if ! [ -e $DIRNAME ]; then
        mkdir -p $DIRNAME
    fi

    cd $DIRNAME
    pydoc -w $i
    cd -
done

exit $?
