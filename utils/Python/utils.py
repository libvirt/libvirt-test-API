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
# Filename: utils.py
# Summary: basic operation on host
# Description: The module is a tool to provide basic operation on host

import os
import re
import sys
import time
import random
import commands
import socket
import fcntl
import struct
import pexpect
import string
import subprocess
from xml.dom import minidom
from urlparse import urlparse

class Utils(object):
    """Basic operation on host"""
    def get_hypervisor(self):
        if commands.getoutput("lsmod | grep kvm"):
            return 'kvm'
        elif os.access("/proc/xen", os.R_OK):
            return 'xen'
        else:
            return 'no any hypervisor is running.'

    def get_uri(self, ip):
        """Get hypervisor uri"""
        hypervisor = self.get_hypervisor()
        if ip == "127.0.0.1":
            if hypervisor == "xen":
                uri = "xen:///"
            if hypervisor == "kvm":
                uri = "qemu:///system"
        else:
            if hypervisor == "xen":
                uri = "xen+ssh://%s" % ip
            if hypervisor == "kvm":
                uri = "qemu+ssh://%s/system" % ip
        return uri

    def parser_uri(self, uri):
        #this is a simple parser for uri
        return urlparse(uri)

    def get_host_arch(self):
        ret = commands.getoutput('uname -a')
        arch = ret.split(" ")[-2]
        return arch

    def get_local_hostname(self):
        """ get local host name """
        return socket.gethostname()

    def get_libvirt_version(self, ver = ''):
        ver = commands.getoutput("rpm -q libvirt|head -1")
        if ver.split('-')[0] == 'libvirt':
            return ver
        else:
            print "Missing libvirt package!"
            sys.exit(1)

    def get_hypervisor_version(self, ver = ''):
        hypervisor = self.get_hypervisor()

        if 'kvm' in hypervisor:
            kernel_ver = self.get_host_kernel_version()
            if 'el5' in kernel_ver:
                ver = commands.getoutput("rpm -q kvm")
            elif 'el6' in kernel_ver:
                ver = commands.getoutput("rpm -q qemu-kvm")
            else:
                print "Unsupported kernel type!"
                sys.exit(1)
        elif 'xen' in hypervisor:
            ver = commands.getoutput("rpm -q xen")
        else:
            print "Unsupported hypervisor type!"
            sys.exit(1)

        return ver

    def get_host_kernel_version(self):
        kernel_ver = commands.getoutput('uname -r')
        return kernel_ver

    def get_ip_address(self, ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(),0x8915, # SIOCGIFADDR
                                struct.pack('256s', ifname[:15]))[20:24])


    def get_host_cpus(self):
        if not os.access("/proc/cpuinfo", os.R_OK):
            print "warning:os error"
            sys.exit(1)
        else:
            cmd = "cat /proc/cpuinfo | grep '^processor'|wc -l"
            cpus = int(commands.getoutput(cmd))
            if cpus:
                return cpus
            else:
                print "warnning:don't get system cpu number"

    def get_host_frequency(self):
        if not os.access("/proc/cpuinfo", os.R_OK):
            print "warning:os error"
            sys.exit(1)
        else:
            cmd = "cat /proc/cpuinfo | grep 'cpu MHz'|uniq"
            cpufreq = commands.getoutput(cmd)
            if cpufreq:
                freq = cpufreq.split(":")[1].split(" ")[1]
                return freq
            else:
                print "warnning:don't get system cpu frequency"

    def get_host_memory(self):
        if not os.access("/proc/meminfo", os.R_OK):
            print "please check os."
            sys.exit(1)
        else:
            cmd = "cat /proc/meminfo | egrep 'MemTotal'"
            ret = commands.getoutput(cmd)
            strMem = ret.split(":")[1]
            mem_num = strMem.split("kB")[0]
            mem_size = int(mem_num.strip())
            if mem_size:
                return mem_size
            else:
                print "warnning:don't get os memory"

    def get_vcpus_list(self):
        host_cpus = self.get_host_cpus()
        max_vcpus = host_cpus * 4
        vcpus_list = []
        n = 0
        while 2**n <= max_vcpus:
            vcpus_list.append(2**n)
            n += 1
        return vcpus_list

    def get_memory_list(self):
        host_mem = self.get_host_memory()
        mem_list = []
        i = 10
        while 2**i*1024 <= host_mem:
            mem_list.append(2**i)
            i += 1
        return mem_list

    def get_curr_time(self):
        curr_time = time.strftime('%Y-%m-%d %H:%M:%S')
        return curr_time

    def get_rand_uuid(self):
        return file('/proc/sys/kernel/random/uuid').readline().strip()

    def get_rand_mac(self):
        mac = []
        mac.append(0x54)
        mac.append(0x52)
        mac.append(0x00)
        i = 0
        while i < 3:
            mac.append(random.randint(0x00, 0xff))
            i += 1
        return ':'.join(map (lambda x: "%02x" % x, mac))

    def get_dom_mac_addr(self, domname):
        """Get mac address of a domain

           Return mac address on SUCCESS or None on FAILURE
        """
        cmd = \
        "virsh dumpxml " + domname \
        + " | grep 'mac address' | awk -F'=' '{print $2}' | tr -d \"[\'/>]\""

        (ret, out) = commands.getstatusoutput(cmd)
        if ret == 0:
            return out
        else:
            return None

    def get_num_vcpus(self, domname):
        """Get mac address of a domain
           Return mac address on SUCCESS or None on FAILURE
        """
        cmd = "virsh dumpxml " + domname + \
        " | grep 'vcpu' | awk -F'<' '{print $2}' | awk -F'>' '{print $2}'"

        (ret, out) = commands.getstatusoutput(cmd)
        if ret == 0:
            return out
        else:
            return None

    def get_size_mem(self, domname):
        """Get mem size of a domain
           Return mem size on SUCCESS or None on FAILURE
        """
        cmd = "virsh dumpxml " + domname + \
        " | grep 'currentMemory'|awk -F'<' '{print $2}'|awk -F'>' '{print $2}'"

        (ret, out) = commands.getstatusoutput(cmd)
        if ret == 0:
            return out
        else:
            return None

    def get_disk_path(self, dom_xml):
        """Get full path of bootable disk image of domain
           Return mac address on SUCCESS or None on FAILURE
        """
        doc = minidom.parseString(dom_xml)
        disk_list = doc.getElementsByTagName('disk')
        source = disk_list[0].getElementsByTagName('source')[0]
        attribute = source.attributes.keys()[0]

        return source.attributes[attribute].value

    def get_capacity_suffix_size(self, capacity):
        dicts = {}
        change_to_byte = {'K':pow(2, 10), 'M':pow(2, 20), 'G':pow(2, 30),
                          'T':pow(2, 40)}
        for suffix in change_to_byte.keys():
            if capacity.endswith(suffix):
                dicts['suffix'] = suffix
                dicts['capacity'] = capacity.split(suffix)[0]
                dicts['capacity_byte'] = \
                int(dicts['capacity']) * change_to_byte[suffix]
        return dicts

    def dev_num(self, guestname, device):
        """Get disk or interface number in the guest"""
        cur = commands.getoutput("pwd")
        cmd = "sh %s/utils/dev_num.sh %s %s" % (cur, guestname, device)
        num = int(commands.getoutput(cmd))
        if num:
            return num
        else:
            return None

    def stop_selinux(self):
        selinux_value = commands.getoutput("getenforce")
        if selinux_value == "Enforcing":
            os.system("setenforce 0")
            if commands.getoutput("getenforce") == "Permissive":
                return "selinux is disabled"
            else:
                return "Failed to stop selinux"
        else:
            return "selinux is disabled"

    def stop_firewall(self, ip):
        stopfire = ""
        if ip == "127.0.0.1":
            stopfire = commands.getoutput("service iptables stop")
        else:
            stopfire = commands.getoutput("ssh %s service iptables stop") %ip
        if stopfire.find("stopped"):
            print "Firewall is stopped."
        else:
            print "Failed to stop firewall"
            sys.exit(1)

    def print_section(self, title):
        print "\n%s" % title
        print "=" * 60

    def print_entry(self, key, value):
        print "%-10s %-10s" % (key, value)

    def print_xml(self, key, ctx, path):
        res = ctx.xpathEval(path)
        if res is None or len(res) == 0:
            value = "Unknown"
        else:
            value = res[0].content
        print_entry(key, value)
        return value

    def print_title(self, info, delimiter, num):
        curr_time = self.get_curr_time()
        blank = ' '*(num/2 - (len(info) + 8 + len(curr_time))/2)
        print delimiter * num
        print "%s%s\t%s" % (blank, info, curr_time)
        print delimiter * num

    def file_read(self, file):
        if os.path.exists(file):
            fh = open(file, 'r')
            theData = fh.read()
            fh.close()
            return theData
        else:
            print "The FILE %s doesn't exist." % file

    def parse_xml(file, element):
        xmldoc = minidom.parse(file)
        elementlist = xmldoc.getElementsByTagName(element)
        return elementlist

    def locate_utils(self):
        """Get the directory path of 'utils'"""
        pwd = os.getcwd()
        result = re.search('(.*)libvirt-test-API(.*)', pwd)
        return result.group(0) + "/utils"

    def mac_to_ip(self, mac, timeout):
        """Map mac address to ip

           Return None on FAILURE and the mac address on SUCCESS
        """
        if not mac:
            return None

        if timeout < 10:
            timeout = 10

        cmd = "sh " + self.locate_utils() + "/ipget.sh " + mac

        while timeout > 0:
            (ret, out) = commands.getstatusoutput(cmd)
            if not out.lstrip() == "":
                break

            timeout -= 10

        return timeout and out or None

    def do_ping(self, ip, timeout):
        """Ping some host

           return True on success or False on Failure
           timeout should be greater or equal to 10
        """
        if not ip:
            return False

        if timeout < 10:
            timeout = 10

        cmd = "ping -c 3 " + str(ip)

        while timeout > 0:
            (ret, out) = commands.getstatusoutput(cmd)
            if ret == 0:
                break
            timeout -= 10

        return (timeout and 1) or 0

    def exec_cmd(self, command, sudo=False, cwd=None, infile=None, outfile=None, shell=False, data=None):
        """
        Executes an external command, optionally via sudo.
        """
        if sudo:
            if type(command) == type(""):
                command = "sudo " + command
            else:
                command = ["sudo"] + command
        if infile == None:
            infile = subprocess.PIPE
        if outfile == None:
            outfile = subprocess.PIPE
        p = subprocess.Popen(command, shell=shell, close_fds=True, cwd=cwd,
                        stdin=infile, stdout=outfile, stderr=subprocess.PIPE)
        (out, err) = p.communicate(data)
        if out == None:
            # Prevent splitlines() from barfing later on
            out = ""
        return (p.returncode, out.splitlines())

    def remote_exec_pexpect(self, hostname, username, password, cmd):
        """ Remote exec function via pexpect """
        user_hostname = "%s@%s" % (username, hostname)
        child = pexpect.spawn("/usr/bin/ssh", [user_hostname, cmd],
                              timeout = 60, maxread = 2000, logfile = None)
        while True:
            index = child.expect(['(yes\/no)', 'password:', pexpect.EOF,
                                 pexpect.TIMEOUT])
            if index == 0:
                child.sendline("yes")
            elif index == 1:
                child.sendline(password)
            elif index == 2:
                child.close()
                return 0, child.before
            elif index == 3:
                child.close()
                return 1, ""

        return 0

    def scp_file(self, hostname, username, password, target_path, file):
        """ Scp file to remote host """
        user_hostname = "%s@%s:%s" % (username, hostname, target_path)
        child = pexpect.spawn("/usr/bin/scp", [file, user_hostname])
        while True:
            index = child.expect(['yes\/no', 'password: ',
                                   pexpect.EOF,
                                   pexpect.TIMEOUT])
            if index == 0:
                child.sendline("yes")
            elif index == 1:
                child.sendline(password)
            elif index == 2:
                child.close()
                return 0
            elif index == 3:
                child.close()
                return 1

        return 0
