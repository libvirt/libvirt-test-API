#!/usr/bin/env python
"""The test scripts will test the function of vcpu affinity of libvirt for 
   virtual machine through calling libvirt python bindings API. 
   mandatory arguments: guestname
                        vcpu
"""

__author__ = "Guannan Ren <gren@redhat.com>"
__date__ = "Fri Apri 16 2010"
__version__ = "0.1.0"
__credits__ = "Copyright (C) 2010 Red Hat, Inc."
__all__ = ['cpu_affinity', 'vcpu_affinity_check', 'set_vcpus', 
           'redefine_vcpu_number', 'check_params'] 

import os
import sys
import re
import time
import commands
import math
from xml.dom import minidom

def append_path(path):
    """Append root path of package"""
    if path in sys.path:
        pass
    else:
        sys.path.append(path)

pwd = os.getcwd()
result = re.search('(.*)libvirt-test-API', pwd)
append_path(result.group(0))

from lib.Python import connectAPI
from lib.Python import domainAPI
from utils.Python import utils
from exception import LibvirtAPI

def check_params(params_given):
    """Checking the arguments required"""
    args_required = ['guestname', 'vcpu']
    for arg in args_required:
        if arg not in params_given.keys():
            logger.error("Argument %s is required." % arg)
            return 1
        elif not params_given[arg]:
            logger.error("value of argument %s is empty" % arg)
            return 1

    return 0

def redefine_vcpu_number(domobj, domain_name, vcpu):
    """dump domain xml description to change the vcpu number,
       then, define the domain again
    """
    guestxml = domobj.get_xml_desc(domain_name)
    logger.debug('''original guest %s xml :\n%s''' %(domain_name, guestxml))

    doc = minidom.parseString(guestxml)

    newvcpu = doc.createElement('vcpu')
    newvcpuval = doc.createTextNode(vcpu)
    newvcpu.appendChild(newvcpuval)

    domain = doc.getElementsByTagName('domain')[0]
    oldvcpu = doc.getElementsByTagName('vcpu')[0]

    domain.replaceChild(newvcpu, oldvcpu)

    return doc.toxml()

def set_vcpus(util, domobj, domain_name, vcpu):
    """set the value of virtual machine to vcpu offline , then boot up
       the virtual machine
    """
    timeout = 60
    logger.info('destroy domain')

    logger.info("get the mac address of vm %s" % domain_name)
    mac = util.get_dom_mac_addr(domain_name)
    logger.info("the mac address of vm %s is %s" % (domain_name, mac))

    logger.info("get ip by mac address")
    ip = util.mac_to_ip(mac, 180)
    logger.info("the ip address of vm %s is %s" % (domain_name, ip))

    try:
        domobj.destroy(domain_name)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
                     (e.response()['message'], e.response()['code']))
        logger.error("fail to destroy domain")
        return 1

    while timeout:
        time.sleep(10)
        timeout -= 10
        logger.info(str(timeout) + "s left")

        logger.info('ping guest')

        if util.do_ping(ip, 30):
            logger.error('The guest is still active, IP: ' + str(ip))
        else:
            logger.info("domain %s is destroied successfully" % domain_name)
            break

    if timeout <= 0:
        logger.error("the domain couldn't be destroied within 60 secs.")
        return 1               

    newguestxml = redefine_vcpu_number(domobj, domain_name, vcpu)
    logger.debug('''new guest %s xml :\n%s''' %(domain_name, newguestxml))

    logger.info("undefine the original guest")
    try:
        domobj.undefine(domain_name)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
                     (e.response()['message'], e.response()['code']))
        logger.error("fail to undefine guest %" % domain_name)
        return 1

    logger.info("define guest with new xml")
    try:
        domobj.define(newguestxml)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
                     (e.response()['message'], e.response()['code']))
        logger.error("fail to define guest %s" % domain_name)
        return 1

    try:
        logger.info('boot guest up ...')
        domobj.start(domain_name)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
                     (e.response()['message'], e.response()['code']))
        logger.error("fail to start domain %s" % domain_name)
        return 1
    
    timeout = 600

    while timeout:
        time.sleep(10)
        timeout -= 10

        ip = util.mac_to_ip(mac, 180)

        if not ip:
            logger.info(str(timeout) + "s left")
        else:
            logger.info("vm %s power on successfully" % domain_name)
            logger.info("the ip address of vm %s is %s" % (domain_name, ip))
            break

    if timeout <= 0:
        logger.info("fail to power on vm %s" % domain_name)
        return 1
 
    return 0

def vcpu_affinity_check(domain_name, vcpu, expected_pinned_cpu, hypervisor):
    """check the task in the process of the running virtual machine
       grep Cpus_allowed_list /proc/PID/task/*/status
    """
    host_kernel_version = utils.Utils().get_host_kernel_version()
    if 'qemu' in hypervisor:
        get_pid_cmd = "cat /var/run/libvirt/qemu/%s.pid" % domain_name
        status, pid = commands.getstatusoutput(get_pid_cmd) 
        if status:
            logger.error("failed to get the pid of \
                          the running virtual machine process")
            return 1
        if 'el6' in host_kernel_version:
            cmd_get_task_list = "grep Cpus_allowed_list /proc/%s/task/*/status" % pid
            status, output = commands.getstatusoutput(cmd_get_task_list) 

            logger.debug("the output of command 'grep Cpus_allowed_list \
                          /proc/%s/task/*/status' is %s" % (pid, output))

            task_list = output.split('\n')[1:]
            vcpu_task = task_list[int(vcpu)]
            actual_pinned_cpu = int(vcpu_task.split('\t')[1], 16)
        elif 'el5' in host_kernel_version:
            cmd_get_task_list = "grep Cpus_allowed /proc/%s/task/*/status" % pid
            status, output = commands.getstatusoutput(cmd_get_task_list) 

            logger.debug("the output of command 'grep Cpus_allowed \
                          /proc/%s/task/*/status' is %s" % (pid, output))

            task_list = output.split('\n')[2:]
            vcpu_task = task_list[int(vcpu)]
            tmp = int(vcpu_task.split('\t')[1].split(',')[-1])
            actual_pinned_cpu = math.log(tmp, 2) 
        else:
            logger.error("unsupported host os version: %s" % host_kernel_version)
            return 1
    elif 'xen' in hypervisor:
        get_expected_pinned_cpu_cmd = "virsh vcpuinfo %s|grep -1 ^VCPU.*[^0-9]%s$|tail -1|cut -d: -f2" % (domain_name, vcpu)
        status, actual_pinned_cpu_str = commands.getstatusoutput(get_expected_pinned_cpu_cmd)
        actual_pinned_cpu = int(actual_pinned_cpu_str)
    else:
        logger.info("unsupported hypervisor type: %s" % hypervisor)
        return 1   
    logger.info("the actual pinned cpu is %s" % actual_pinned_cpu) 
    shell_cmd = "virsh vcpuinfo %s" % domain_name
    (status, text) = commands.getstatusoutput(shell_cmd)
    logger.debug("after pinning, the vcpu status is %s" % text)

    if actual_pinned_cpu == expected_pinned_cpu:
        logger.info("actual_pinned_physical_cpu is \
                     equal to expected_pinned_physical_cpu")
        return 0
    else:
        logger.info("actual_pinned_physical_cpu is \
                     not equal to expected_pinned_physical_cpu")
        return 1

def cpu_affinity(params):
    """set vcpu of virtual machine to value of parameter vcpu
       call libvirt API function to set cpu affinity
       check the result after cpupin
    """
    # Initiate and check parameters
    global logger 
    logger = params['logger']
    params.pop('logger')
    params_check_result = check_params(params)
    if params_check_result: 
        return 1  
    domain_name = params['guestname']
    vcpu = params['vcpu']

    logger.info("the name of virtual machine is %s" % domain_name)
    logger.info("the vcpu given is %s" % vcpu)

    # Connect to local hypervisor connection URI
    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')
    virconn = connectAPI.ConnectAPI().open(uri)
    hypervisor = uri.split(':')[0]
   
    # Get cpu affinity 
    domobj = domainAPI.DomainAPI(virconn)
    dom_name_list = domobj.get_list()
    if domain_name not in dom_name_list:
        logger.error("guest %s doesn't exist or not be running." % 
                      domain_name)
        return 1

    vcpunum = util.get_num_vcpus(domain_name)
    logger.info("the current vcpu number of guest %s is %s" % \
                (domain_name, vcpunum))    

    if vcpunum != vcpu:
        logger.info("set the vcpu of the guest to %s" % vcpu)
        ret = set_vcpus(util, domobj, domain_name, vcpu)            
        if ret != 0:
            return 1

    vcpunum_after_set = util.get_num_vcpus(domain_name)
    logger.info("after setting, the current vcpu number the guest is %s" % \
                 vcpunum_after_set)
    vcpu_list = range(int(vcpunum_after_set))

    physical_cpu_num = util.get_host_cpus()
    logger.info("in the host, we have %s physical cpu" % physical_cpu_num)

    cpu_affinity = ()
    for i in range(physical_cpu_num):
        cpu_affinity = cpu_affinity + (False,)
                       
    retflag = 0
    for i in range(physical_cpu_num):
        cpu_affinity_test = ()
        for affinity_num in range(len(cpu_affinity)):
            if affinity_num == i:
                cpu_affinity_test = cpu_affinity_test + (True,)
            else:
                cpu_affinity_test = cpu_affinity_test + \
                                    (cpu_affinity[affinity_num],)

        logger.debug("the data for testing is")        
        logger.debug(cpu_affinity_test)

        for vcpu_pinned in vcpu_list:
            try:
                logger.info("Now, we pin vcpu %s to physical vcpu %s" % 
                            (vcpu_pinned, i))

                shell_cmd = "virsh vcpuinfo %s" % domain_name
                text = commands.getstatusoutput(shell_cmd)[1]
                logger.debug("before pinning, the vcpu status is %s" % text)

                domobj.set_pin_vcpu(domain_name, vcpu_pinned, 
                                    cpu_affinity_test)
            except LibvirtAPI, e:
                logger.error("API error message: %s, error code is %s" % \
                             (e.response()['message'], e.response()['code']))
                logger.error("fail to vcpupin domain")
                return 1
            ret = vcpu_affinity_check(domain_name, vcpu_pinned, i, hypervisor)
            retflag = retflag + ret
            if ret:
                logger.error("vcpu affinity checking failed.")
            else:
                logger.info("vcpu affinity checking successed.")
 
    if retflag:
        return 1
    else:
        return 0

