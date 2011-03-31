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
# Filename: log.py 
# Summary: log file operation 
# Description: The module is a tool to provide basic log file operation 
# Maintainer: ajia@redhat.com
# Update: Oct 23 2009
# Version: 0.1.0

import time
import os
import logging

class Log(object):
    """Log file operation"""
    counter = 0
    number = 0
    log_list = list()
    fat_dict = {'file_formatter': 
                '[%(asctime)s] %(process)d %(levelname)-8s \
                 (%(module)s:%(lineno)d) %(message)s',
                'console_formatter': 
                '%(name)-8s | %(levelname)-8s | %(message)s'}
    @staticmethod
    
    def get_log_name():
        """Get log file name"""
        Log.counter += 1
        logname = ''
        if Log.counter > 0 and Log.counter <= 9:
            base_str = 'libvirt_test00'
            logname = base_str + str(Log.counter)            

        if Log.counter > 9 and Log.counter <= 99:
            base_str = 'libvirt_test0'
            logname = base_str + str(Log.counter)

        if Log.counter > 99 and Log.counter <= 999:
            base_str = 'libvirt_test'
            logname = base_str + str(Log.counter)
        return logname
 
    def __init__(self, logname):
        self.name = logname

    def init_log(self, flag = 0):
        """Initialize log file"""
        file_formatter = console_formatter = ''
        if flag == 0:
            file_formatter = Log.fat_dict['file_formatter']
            console_formatter = Log.fat_dict['console_formatter']
        else:
            file_formatter = '' 
            console_formatter = ''
        reload(logging)
        logging.basicConfig(level = logging.DEBUG,
                            format = file_formatter,
                            datefmt = '%Y-%m-%d %H:%M:%S',
                            filename = self.name,
                            filemode = 'a+')
        logger = logging.getLogger(self.name)
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        
        formatter = logging.Formatter(console_formatter)
        console.setFormatter(formatter)
        logger.addHandler(console)
        return logger

