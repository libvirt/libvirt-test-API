#!/usr/bin/env python
#
#
# Filename: process.py
# Summary: multiprocessing module
# Description: If the switch of multiprocessing is on,
#              the module will be called to fork subprocess

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

