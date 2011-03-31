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
# Filename: process.py 
# Summary: multiprocessing module 
# Description: If the switch of multiprocessing is on,
#              the module will be called to fork subprocess 
# Maintainer: jyang@redhat.com
# Updated: Oct 19 2009
# Version: 0.1.0

import os
import sys
import time
import errno

class Process:
    def __init__(self, list):
        self.procs = list
        self.pids = []

    def fork(self):
        for i in self.procs:
            pid = os.fork()
            if 0 == pid:
                ret = i()
                os._exit(ret)
            elif 0 < pid:
                self.pids.append(pid)
            else:
                print "ERROR: Failed on forking process"
                sys.exit(1)

    def wait(self):
        passnum = 0
        failnum = 0
        for i in self.pids:
            pid, ret = os.waitpid(i, 0)

            if ret:
                failnum += 1
            else:
                passnum += 1
        return passnum, failnum

