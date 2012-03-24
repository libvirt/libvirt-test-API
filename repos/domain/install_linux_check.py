#!/usr/bin/env python
"""The test script is for installing a new guest virtual machine
   via calling libvirt python bindings API.
   mandatory arguments:guesttype
                       guestname
                       netmethod
   optional arguments: memory
                       vcpu
                       disksize
                       imagepath
                       hdmodel
                       nicmodel
                       ifacetype
                       source
                       type: define|create
"""

__author__ = "Jianlin Liu <jialiu@redhat.com>"
__date__ = "Wed Jul 05 2010"
__version__ = "0.1.0"
__credits__ = "Copyright (C) 2010 Red Hat, Inc."
__all__ = ['install_linux_check', 'usage']

import os
import sys
import re
import time
import copy
import math

def append_path(path):
    """Append root path of package"""
    if path in sys.path:
        pass
    else:
        sys.path.append(path)

pwd = os.getcwd()
result = re.search('(.*)libvirt-test-API', pwd)
homepath = result.group(0)
append_path(homepath)

from lib import connectAPI
from lib import domainAPI
from utils.Python import utils
from utils.Python import check
from utils.Python import env_parser

def usage():
    print '''usage: mandatory arguments:guestname
                           guesttype
                           hdmodel
                           nicmodel
       optional arguments: disksize
                           memory
                           vcpu
                           guesttype
                           imagepath
                           ifacetype
                           netmethod
                           source
                           type
          '''

def check_params(params):
    """Checking the arguments required"""
    params_given = copy.deepcopy(params)
    mandatory_args = ['guestname', 'guesttype', 'hdmodel', 'nicmodel']
    optional_args = ['disksize', 'memory', 'vcpu', 'guesttype',
                     'imagepath', 'ifacetype', 'netmethod', 'source', 'type']

    for arg in mandatory_args:
        if arg not in params_given.keys():
            logger.error("Argument %s is required." % arg)
            usage()
            return 1
        elif not params_given[arg]:
            logger.error("value of argument %s is empty." % arg)
            usage()
            return 1

        params_given.pop(arg)

    if len(params_given) == 0:
        return 0

    for arg in params_given.keys():
        if arg not in optional_args:
            logger.error("Argument %s could not be recognized." % arg)
            return 1

    return 0

def install_linux_check(params):
    """check guest status after installation, including network ping,
       read/write option in guest. return value: 0 - ok; 1 - bad
    """
    # Initiate and check parameters
    global logger
    logger = params['logger']
    params.pop('logger')
    logger.info("Checking the validation of arguments provided.")
    params_check_result = check_params(params)
    if params_check_result:
        return 1

    logger.info("Arguments checkup finished.")

    guestname = params.get('guestname')
    guesttype = params.get('guesttype')

    logger.info("the name of guest is %s" % guestname)

    # Connect to local hypervisor connection URI
    util = utils.Utils()
    hypervisor = util.get_hypervisor()
    uri = params['uri']

    logger.info("the type of hypervisor is %s" % hypervisor)
    logger.debug("the uri to connect is %s" % uri)

    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)
    domobj = domainAPI.DomainAPI(virconn)
    state = domobj.get_state(guestname)
    conn.close()

    if(state == "shutoff"):
        logger.info("guest is shutoff, if u want to run this case, \
                     guest must be started")
        return 1

    logger.info("get the mac address of vm %s" % guestname)
    mac = util.get_dom_mac_addr(guestname)
    logger.info("the mac address of vm %s is %s" % (guestname, mac))

    timeout = 300
    while timeout:
        ipaddr = util.mac_to_ip(mac, 180)
        if not ipaddr:
            logger.info(str(timeout) + "s left")
            time.sleep(10)
            timeout -= 10
        else:
            logger.info("the ip address of vm %s is %s" % (guestname, ipaddr))
            break

    if timeout == 0:
        logger.info("vm %s fail to get ip address" % guestname)
        return 1

    time.sleep(120)

    logger.info("Now checking guest health after installation")

    domain_name=guestname
    blk_type=params['hdmodel']
    nic_type=params['nicmodel']
    chk = check.Check()
    Test_Result = 0

    # Ping guest from host
    logger.info("check point1: ping guest from host")
    if util.do_ping(ipaddr, 20) == 1:
        logger.info("ping current guest successfull")
    else:
        logger.error("Error: can't ping current guest")
        Test_Result = 1
        return Test_Result

    # Creat file and read file in guest.
    logger.info("check point2: creat and read dirctory/file in guest")
    if chk.create_dir(ipaddr, "root", "redhat") == 0:
        logger.info("create dir - /tmp/test successfully")
        if chk.write_file(ipaddr, "root", "redhat") == 0:
            logger.info("write and read file: /tmp/test/test.log successfully")
        else:
            logger.error("Error: fail to write/read file - /tmp/test/test.log")
            Test_Result = 1
            return Test_Result
    else:
        logger.error("Error: fail to create dir - /tmp/test")
        Test_Result = 1
        return Test_Result

    # Check whether vcpu equals the value set in geust config xml
    logger.info("check point3: check cpu number in guest equals to \
                 the value set in domain config xml")
    vcpunum_expect = int(util.get_num_vcpus(domain_name))
    logger.info("vcpu number in domain config xml - %s is %s" % \
                 (domain_name, vcpunum_expect))
    vcpunum_actual = int(chk.get_remote_vcpus(ipaddr, "root", "redhat"))
    logger.info("The actual vcpu number in guest - %s is %s" %
                 (domain_name, vcpunum_actual))
    if vcpunum_expect == vcpunum_actual:
        logger.info("The actual vcpu number in guest is \
                     equal to the setting your domain config xml")
    else:
        logger.error("Error: The actual vcpu number in guest is \
                      NOT equal to the setting your domain config xml")
        Test_Result = 1
        return Test_Result

    # Check whether mem in guest is equal to the value set in domain config xml
    logger.info("check point4: check whether mem in guest is equal to \
                 the value set in domain config xml")
    mem_expect = util.get_size_mem(domain_name)
    logger.info("current mem size in domain config xml - %s is %s" %
                 (domain_name, mem_expect))
    mem_actual = chk.get_remote_memory(ipaddr, "root", "redhat")
    logger.info("The actual mem size in guest - %s is %s" %
                (domain_name, mem_actual))
    diff_range = int(mem_expect) * 0.07
    diff = int(mem_expect) - int(mem_actual)
    if int(math.fabs(diff)) < int(diff_range):
        logger.info("The actual mem size in guest is almost equal to \
                    the setting your domain config xml")
    else:
        logger.error("Error: The actual mem size in guest is NOT equal to \
                      the setting your domain config xml")
        Test_Result = 1
        return Test_Result

    # Check app works fine in guest, such as: wget
    logger.info("check point5: check app works fine in guest, such as: wget")
    logger.info("get system environment information")
    envfile = os.path.join(homepath, 'env.cfg')
    logger.info("the environment file is %s" % envfile)

    envparser = env_parser.Envparser(envfile)
    file_url = envparser.get_value("other", "wget_url")

    if chk.run_wget_app(ipaddr, "root", "redhat", file_url, logger) == 0:
        logger.info("run wget successfully in guest.")
    else:
        logger.error("Error: fail to run wget in guest")
        Test_Result = 1
        return Test_Result

    # Check nic and blk driver in guest
    if 'kvm' in guesttype or 'xenfv' in guesttype:
        logger.info("check point6: check nic and blk driver in guest is \
                     expected as your config:")
        if chk.validate_remote_nic_type(ipaddr, "root", "redhat",
           nic_type, logger) == 0 and \
           chk.validate_remote_blk_type(ipaddr, "root", "redhat",
                                        blk_type, logger) == 0:
            logger.info("nic type - %s and blk type - %s check successfully" %
                       (nic_type, blk_type))
        else:
            logger.error("Error: nic type - %s or blk type - %s check failed" %
                        (nic_type, blk_type))
            Test_Result = 1
            return Test_Result

    util.clean_ssh()

    return Test_Result

def install_linux_check_clean(params):
    """ clean testing environment """
    pass

