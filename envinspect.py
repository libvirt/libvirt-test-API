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
# Filename: envinspect.py 
# Summary: To generate a callable class for clearing testing environment  
# Description: The module match the reference of clearing function 
#              from each testcase to the corresponding testcase's 
#              argument in the order of testcase running 
# Maintainer: gren@redhat.com
# Updated: Apr 10 2011
# Version: 0.1.0

import subprocess

def childprocess(pcmd, acmd):
    P1 = subprocess.Popen(pcmd, stdout = subprocess.PIPE)
    P2 = subprocess.Popen(acmd, stdin = P1.stdout, stdout =subprocess.PIPE)
    out = P2.communicate()[0].strip()
    rc = P2.returncode

    if rc == 0:
        return out
    else:
        return ""

def get_libvirt_ver():
    ver = childprocess(['rpm', '-qa'], ['egrep', "^libvirt-[0-9]"])
    if ver == "":
        return 100, "No libvirt installed, necessary"
    else:
        return 0, ver

def get_libvirt_pyth_ver():
    ver = childprocess(['rpm', '-qa'], ['egrep', "^libvirt-python-[0-9]"])
    if ver == "":
        return 100, "No libvirt-python installed, necessary"
    else:
        return 0, ver

def get_libvirt_cli_ver():
    ver = childprocess(['rpm', '-qa'], ['egrep', "^libvirt-client-[0-9]"])
    if ver == "":
        return 100, "No libvirt-client installed, necessary"
    else:
        return 0, ver

def get_qemu_kvm_ver():
    ver = childprocess(['rpm', '-qa'], ['egrep', "qemu-kvmd-[0-9]"])
    if ver == "":
        return 150, "No qemu-kvm installed, optional"
    else:
        return 0, ver

def get_kernel_ver():
    ver = childprocess(['rpm', '-qa'], ['egrep', "^kernel-[0-9]"])
    if ver == "":
        return 100, "No kernel installed, necessary"
    else:
        return 0, ver


class EnvInspect(object):
    """to check and collect the testing enviroment infomation
       before performing testing
    """
    
    def __init__(self, logger):
        self.logger = logger

    def env_checking(self):
        flag = 0
        self.logger.info(get_libvirt_ver()[1])
        if get_libvirt_ver()[0] == 100: flag = 1
        self.logger.info(get_libvirt_pyth_ver()[1])
        if get_libvirt_pyth_ver()[0] == 100: flag = 1
        self.logger.info(get_libvirt_cli_ver()[1])
        if get_libvirt_cli_ver()[0] == 100: flag = 1
        self.logger.info(get_qemu_kvm_ver()[1])
        if get_qemu_kvm_ver()[0] == 150 and flag == 0: 
            flag = 0
        elif get_qemu_kvm_ver()[0] == 150 and flag == 1:
            flag = 1
        else:
            pass
        self.logger.info(get_kernel_ver()[1])
        if get_kernel_ver()[0] == 100: flag = 1
        return flag 
        

