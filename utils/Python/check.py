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
# Filename: check.py 
# Summary: basic check operation needed by test 
# Description: The module is a tool to help conduct basic 
#              check operation on specified host 

import os
import re
import time
import string
import pty
import commands
import signal
import pexpect

class Check(object):
    """Basic check operation for test"""
    def support_virt(self):
        cmd = "cat /proc/cpuinfo | egrep '(vmx|svm)'"
        if commands.getoutput(cmd) is None:
            print 'CPU does not support VT.'
            return False
        else:
            return True

    def __init__( self, subproc_pid = 0, subproc_flag = 0 ):
        self.subproc_flag = subproc_flag

    def subproc(self, a, b):
        self.subproc_flag = 1
    
    def remote_exec(self, hostname, username, password, cmd):
        """Remote execution on specified host"""
        pid, fd = pty.fork()
        if pid == 0:
            try:
                os.execv("/usr/bin/ssh", ["/usr/bin/ssh", "-l", 
                         username, hostname, cmd])
            except OSError, e:
                print "OSError: " + str(e)
                return -1
        else:
            signal.signal(signal.SIGCHLD, self.subproc)
            try:
                timeout = 50
                i = 0
                while  i <= timeout:

                    time.sleep(1)
                    str = os.read(fd, 10240)
                        
                    if re.search('(yes\/no)', str):
                        os.write(fd, "yes\r")
                                
                    elif re.search('password:', str):
                        os.write(fd, password + "\r")

                    elif self.subproc_flag == 1:
                        ret = string.strip(str)
                        break
                    elif i == timeout:
                        print "TIMEOUT!!!!"
                        return -1
                        
                    i = i+1

                self.subproc_flag = 0
                return ret
            except Exception, e:
                self.subproc_flag = 0
                return -1

    def remote_exec_pexpect(self, hostname, username, password, cmd):
        """Remote exec function via pexpect"""
        user_hostname = "%s@%s" % (username, hostname)
        child = pexpect.spawn("/usr/bin/ssh", [user_hostname, cmd], 
                              timeout = 60, maxread = 2000, logfile = None)
        #child.logfile = sys.stdout
        while True:
            index = child.expect(['(yes\/no)', 'password:', pexpect.EOF, 
                                 pexpect.TIMEOUT])
            if index == 0:
                child.sendline("yes")
            elif index == 1:
                child.sendline(password)
            elif index == 2:
                return string.strip(child.before)
            elif index == 3:
                return "TIMEOUT!!!"

    def get_remote_vcpus(self, hostname, username, password):
        """Get cpu number of specified host"""
        cmd = "cat /proc/cpuinfo | grep processor | wc -l"
        cpunum = -1
        i = 0
        while i < 3:
            i += 1
            cpunum = int(self.remote_exec(hostname, username, password, cmd))
            if cpunum == -1:
                continue
            else:
                break
        return cpunum
    
    def get_remote_memory(self, hostname, username, password):
        """Get memory statics of specified host"""
        cmd = "free -m | grep -i mem | awk '{print $2}'"
        memsize = -1
        i = 0
        while i < 3:
            i += 1
            memsize = \
            int(self.remote_exec_pexpect(hostname, username, password, cmd)) * 1024
            if memsize == -1:
                continue
            else:
                break
        return memsize

    def get_remote_kernel(self, hostname, username, password):
        """Get kernel info of specified host"""
        cmd = "uname -r"
        kernel = None
        i = 0
        while i < 3:
            i += 1
            kernel = self.remote_exec(hostname, username, password, cmd)
            if kernel:
                break
            else:
                continue
        return kernel

    def install_package(self, package = ''):
        """Install specified package"""
        if package:
            cmd = "rpm -qa " + package
            output = commands.getoutput(cmd)
            pkg = output.split('\n')[0]
            if pkg:
                os.system("yum -y -q update " + package)
                return pkg
            else:
                ret = os.system("yum -y -q install " + package)
                if ret == 0:
                    output = commands.getoutput(cmd)
                    pkg = output.split('\n')[0]
                    if pkg:
                        return pkg
                else:
                    return "failed to install package"
        else:
            return "please input package name"

    def libvirt_version(self, latest_ver = ''):
        """Get libvirt version info"""
        query_virt_ver = 'rpm -qa|grep libvirt'
        ret = commands.getoutput(query_virt_ver)
        if ret:
            mas_ver = ret.split('-')[-2]
            sec_ver = (ret.split('-')[-1])
            curr_ver = mas_ver + '-' + sec_ver
            if latest_ver != '':
                if curr_ver != latest_ver:
                    return (False, curr_ver)
                else:
                    return (True, curr_ver)
            else:
                return curr_ver
        else:
            return (False, '')

    def create_dir(self, hostname, username, password):
        """Create new dir"""
        cmd = "mkdir /tmp/test"
        mkdir_ret = self.remote_exec_pexpect(hostname, username, password, cmd)
        if mkdir_ret == '':
            cmd = "ls -d /tmp/test"
            check_str = self.remote_exec_pexpect(hostname, username, 
                                                 password, cmd)
            if check_str == "/tmp/test":
                return 0
            else:
                print "check_str = ", check_str
                return 1
        else:
            print "mkdir_ret = ", mkdir_ret
            return 1

    def write_file(self, hostname, username, password):
        """Simple test for writting file on specified host"""
        test_string = 'hello word testing'
        cmd = """echo '%s'>/tmp/test/test.log""" % (test_string)
        write_file_ret = self.remote_exec_pexpect(hostname, username, 
                                                  password, cmd)
        if write_file_ret == '':
            cmd = """grep '%s' /tmp/test/test.log""" % ("hello")
            check_str = self.remote_exec_pexpect(hostname, username, 
                                                 password, cmd)
            if check_str == test_string:
                return 0
            else:
                print "check_str = ", check_str
                return 1
        else:
            print "write_file_ret = ", write_file_ret
            return 1

    def run_mount_app(self, hostname, username, password, 
                      target_mount, mount_point):
        """Simple test for mount operation on specified host"""
        cmd = """mount %s %s""" % (target_mount, mount_point)
        mount_ret = self.remote_exec(hostname, username, password, cmd)
        if mount_ret == '':
            cmd = """df | grep '%s'""" % (target_mount)
            check_str = self.remote_exec(hostname, username, password, cmd)
            if check_str != '':
                return 0
            else:
                print "mount check fail"
                return 1
        else:
            print "mount fail"
            return 1

    def run_wget_app(self, hostname, username, password, file_url, logger):
        """Simple test for wget app on specified host"""
        cmd_line = "wget -P /tmp %s -o /tmp/wget.log" % (file_url)
        logger.info("Command: %s" % (cmd_line))
        wget_ret = self.remote_exec_pexpect(hostname, username, 
                                            password, cmd_line)
        cmd_line = "grep %s %s" % ('100%', '/tmp/wget.log')
        check_ret = self.remote_exec_pexpect(hostname, username, 
                                             password, cmd_line)
        if check_ret == "":
            logger.info("grep output is nothing")
            return 1
        else:
            if re.search("100%", check_ret):
                logger.info("wget is running successfully")
                logger.info("check_retrun: %s" % (check_ret))
                return 0
            else:
                logger.info("can not find 100% in wget output")
                logger.info("check_retrun: %s" % (check_ret))
                return 1

    def validate_remote_nic_type(self, hostname, username, 
                                 password, nic_type, logger):
        """Validate network interface type on specified host"""
        nic_type_to_name_dict = {'e1000':
                                 'Intel Corporation \
                                  82540EM Gigabit Ethernet Controller', 
                                 'rtl8139':
                                 'Realtek Semiconductor Co., Ltd. \
                                  RTL-8139/8139C/8139C+', 
                                 'virtio':'Virtio network device'}
        nic_type_to_driver_dict = {'e1000':'e1000', 'rtl8139':'8139cp',
                                  'virtio':'virtio_net'}
        nic_name = nic_type_to_name_dict[nic_type]
        nic_driver = nic_type_to_driver_dict[nic_type]
        logger.info("nic_name = %s" % (nic_name))
        logger.info("nic_driver = %s" % (nic_driver))
        lspci_cmd = "lspci"
        lsmod_cmd = "lsmod"
        lspci_cmd_ret = self.remote_exec_pexpect(hostname, username, 
                                                 password, lspci_cmd)
        lsmod_cmd_ret = self.remote_exec_pexpect(hostname, username, 
                                                 password, lsmod_cmd)
        logger.info("------------")
        logger.info("lspci_cmd_ret:\n %s" % (lspci_cmd_ret))
        logger.info("------------")
        logger.info("lsmod_cmd_ret:\n %s" % (lsmod_cmd_ret))
        logger.info("------------")
        if lspci_cmd_ret != "" and lsmod_cmd_ret != "":
            cmd1 = """echo "%s" | grep '%s'""" % (lspci_cmd_ret, nic_name) 
            cmd2 = """echo "%s" | grep '%s'""" % (lsmod_cmd_ret, nic_driver)
            status1, output1 = commands.getstatusoutput(cmd1)
            status2, output2 = commands.getstatusoutput(cmd2)
            if status1 == 0 and status2 == 0:
                # other nic should not be seen in guest
                nic_type_to_name_dict.pop(nic_type)
                for key in nic_type_to_name_dict.keys():
                    logger.info("now try to grep other nic type \
                                in lspci output: %s" % key)
                    other_name_cmd = """echo '%s' | grep '%s'""" % \
                                     (lspci_cmd_ret, nic_type_to_name_dict[key])
                    ret, out = commands.getstatusoutput(other_name_cmd)
                    if ret == 0:
                        logger.info("unspecified nic name is seen in \
                                   guest's lspci command: \n %s \n" % out)
                        return 1

                nic_type_to_driver_dict.pop(nic_type)
                for key in nic_type_to_driver_dict.keys():
                    logger.info("now try to grep other nic type \
                              in lsmod output: %s" % key)
                    other_driver_cmd = """echo '%s' | grep '%s'""" % \
                                   (lsmod_cmd_ret, 
                                    nic_type_to_driver_dict[key])
                    ret1, out1 = commands.getstatusoutput(other_driver_cmd)
                    if ret1 == 0:
                        logger.info("unspecified nic driver is seen \
                                   in guest's lsmod command: %s" % out)
                        return 1
             
                logger.info("lspci ouput about nic is: \n %s; \n \
                            lsmod output about nic is \n %s \n" %
                            (output1,output2))
                return 0
            else:
                logger.info("lspci and lsmod and grep fail")
                return 1 
        else:
            logger.info("lspci and lsmod return nothing")
            return 1

    def validate_remote_blk_type(self, hostname, username, password, 
                                 blk_type, logger):
        """Validate block device type on specified host"""
        blk_type_to_name_dict = {'ide':'Intel Corporation 82371SB PIIX3 IDE',
                                 'virtio':'Virtio block device'}
        blk_type_to_driver_dict = {'ide':'unknow', 'virtio':'virtio_blk'}
        lspci_cmd = "lspci"
        lsmod_cmd = "lsmod"
        lspci_cmd_ret = self.remote_exec_pexpect(hostname, username, 
                                                 password, lspci_cmd)
        lsmod_cmd_ret = self.remote_exec_pexpect(hostname, username, 
                                                password, lsmod_cmd)
        logger.info("------------")
        logger.info("lspci_cmd_ret:\n %s" % (lspci_cmd_ret)) 
        logger.info("------------")
        logger.info("lsmod_cmd_ret: \n %s" % (lsmod_cmd_ret))
        logger.info("------------")
        if lspci_cmd_ret != "" and lsmod_cmd_ret != "":
            if blk_type == "virtio":
                blk_name = blk_type_to_name_dict[blk_type]
                blk_driver = blk_type_to_driver_dict[blk_type]
                logger.info("blk_name = %s \n blk_driver = %s" %
                            (blk_name, blk_driver))
                cmd1 = """echo "%s" | grep '%s'""" % (lspci_cmd_ret, blk_name)
                cmd2 = """echo "%s" | grep '%s'""" % (lsmod_cmd_ret, blk_driver)
                status1, output1 = commands.getstatusoutput(cmd1)
                status2, output2 = commands.getstatusoutput(cmd2)
                if status1 == 0 and status2 == 0:
                    logger.info("block device type is virtio")
                    return 0
                else:
                    return 1

          # this check will not check ide type block device
            if blk_type == "ide":
                # virtio block device should not be seen in guest
                blk_type_to_name_dict.pop(blk_type)
                for key in blk_type_to_name_dict.keys():
                    logger.info(
                        "now try to grep other blk type in lspci output: %s" %
                        key)
                    other_name_cmd = """echo "%s" | grep '%s'""" % \
                                     (lspci_cmd_ret, blk_type_to_name_dict[key])
                    ret, out = commands.getstatusoutput(other_name_cmd)
                    if ret == 0:
                        logger.info("unspecified blk name is seen in guest's \
                                    lspci command: \n %s \n" % out)
                        return 1
                blk_type_to_driver_dict.pop(blk_type)
                for key in blk_type_to_driver_dict.keys():
                    logger.info(
                        "now try to grep other blk type in lsmod output: %s" %
                        key)
                    other_driver_cmd = """echo '%s' | grep '%s'""" % \
                                       (lsmod_cmd_ret,
                                       blk_type_to_driver_dict[key])
                    ret1, out1 = commands.getstatusoutput(other_driver_cmd)
                    if ret1 == 0:
                        logger.info("unspecified blk driver is seen \
                                    in guest's lsmod command: \n %s \n" % out)
                        return 1
                logger.info("block device type is ide")
                return 0
        else:
            logger.info("lspci and lsmod return nothing")
            return 1

