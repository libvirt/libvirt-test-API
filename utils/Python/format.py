#!/usr/bin/env python
#
# libvirt-test-API is copyright 2010 Red Hat, Inc.
#
# libvirt-test-API is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version. This program is distributed in
# the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranties of TITLE, NON-INFRINGEMENT,
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# The GPL text is available in the file COPYING that accompanies this
# distribution and at <http://www.gnu.org/licenses>.
#
# Filename: format.py
# Summary: generate specified kind of format string
# Description: The module is a tool to generate specified kind of format string

from string import Template

class Format(object):
    """This class is used for output kinds of format string"""
    def __init__(self, logname):
        self.logname = logname

    def write_log(self, msg):
        """Write log file"""
        fp = open(self.logname, 'a+')
        fp.write(msg)
        fp.close()

    def printf(self, format, *args):
        """The function is dispather,which uses prefix print_ cat
           format to construct function call,and its argument is
           varible long
        """
        exec_func = getattr(self, "print_%s" %format)
        if len(args) == 1:
            for arg in args:
                return exec_func(arg)
        elif len(args) == 2:
            arg1, arg2 = args
            return exec_func(arg1, arg2)
        else:
            arg1, arg2, arg3 = args
            return exec_func(arg1, arg2, arg3)

    def print_title(self, msg, delimiter = '-', num = 128):
        """Print a string title"""
        blank = ' '*((num - len(msg))/2)
        delimiters =  delimiter * num
        lists = list()
        lists.append(blank)
        lists.append(msg)
        msg = ''.join(lists)
        msgs = "\n%s\n%s\n%s" % (delimiters, msg, delimiters)
        print msgs
        self.write_log(msgs)

    def print_string(self, msg):
        """Only print a simple string"""
        print msg
        self.write_log('\n%s' %msg)

    def print_start(self, msg):
        """When test case starting,this function is called"""
        console = "    %s" % msg
        num = (128 - len(msg))/2 - 2
        tpl = Template("\n$sep   $str  $sep\n")
        msgs = tpl.substitute(sep = '-'*num, str = msg)
        print console
        self.write_log(msgs)

    def print_end(self, msg, flag):
        """When test case finishing,this function is called"""
        result = ''
        if flag == 0:
            result = 'PASS'
            console_result = '\033[1;36mOK\033[1;m'
        if flag == 1:
            result = 'FAIL'
            console_result = '\033[1;31mFAIL\033[1;m'
        if flag == 100:
            result = 'Skip'
            console_result = '\033[1;38mSkip\033[1;m'

        console = "            Result: %s\n" % console_result
        msg = msg + ' ' + result
        num = (128 - len(msg))/2 - 2
        tpl = Template("$sep   $str  $sep")
        msgs = tpl.substitute(sep = '-'*num, str = msg)
        print console,
        self.write_log(msgs)
        separator = '\n' + '-' * 128 + '\n'
        self.write_log(separator)

