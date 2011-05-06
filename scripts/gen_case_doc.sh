#! /bin/sh
# Create documentation of cases in Python

FILES=`find $PWD/repos/Python -type f -name "*.py"`

for i in ${FILES}; do
    if [ $(basename $i) != '__init__.py' ]; then
        DIRNAME=$(dirname $i)
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
