#!/usr/bin/env python
"""The test scripts will test the balloon memory feature of libvirt for
   virtual machine through calling libvirt python bindings API.
   mandatory arguments: guestname
                        memorypair
"""

import os
import sys
import re
import time
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

from lib import connectAPI
from lib import domainAPI
from utils.Python import utils
from utils.Python import check
from exception import LibvirtAPI

__author__ = "Guannan Ren <gren@redhat.com>"
__date__ = "Thu April 01 2010"
__version__ = "0.1.0"
__credits__ = "Copyright (C) 2010 Red Hat, Inc."
__all__ = ['balloon_memory', 'usage']

def return_close(conn, logger, ret):
    conn.close()
    logger.info("closed hypervisor connection")
    return ret

def check_params(params_given):
    """Checking the arguments required"""

    args_required = ['guestname', 'memorypair']

    for arg in args_required:
        if arg not in params_given.keys():
            logger.error("Argument %s is required." % arg)
            return 1
        elif not params_given[arg]:
            logger.error("value of argument %s is empty" % arg)
            return 1

    return 0

def get_mem_size(ip):
    """ get current memory size in guest virtual machine"""

    username = 'root'
    password = 'redhat'
    checking = check.Check()
    current_memory = checking.get_remote_memory(ip, username, password)
    return current_memory

def compare_memory(expect_memory, actual_memory):
    """ comparing expected memory size with actual memory size """

    logger.info("expected memory size is %s" % expect_memory)
    logger.info("actual memory size is %s" % actual_memory)
    diff = int(expect_memory) - int(actual_memory)

    if int(math.fabs(diff)) < 50000:
        return 0
    else:
        return 1

def redefine_memory_size(domobj, domain_name, memsize):
    """ dump domain xml description to change the memory size,
        then, define the domain again
    """
    guestxml = domobj.get_xml_desc(domain_name)
    logger.debug('''original guest %s xml :\n%s''' %(domain_name, guestxml))

    doc = minidom.parseString(guestxml)

    newmem = doc.createElement('memory')
    newmemval = doc.createTextNode(str(memsize))
    newmem.appendChild(newmemval)

    newcurmem = doc.createElement('currentMemory')
    newcurmemval = doc.createTextNode(str(memsize))
    newcurmem.appendChild(newcurmemval)

    domain = doc.getElementsByTagName('domain')[0]
    oldmem = doc.getElementsByTagName('memory')[0]
    oldcurmem = doc.getElementsByTagName('currentMemory')[0]

    domain.replaceChild(newmem, oldmem)
    domain.replaceChild(newcurmem, oldcurmem)

    return doc.toxml()

def guest_power_on(domobj, domain_name, mac):
    """ power on guest virtual machine"""

    try:
        domobj.start(domain_name)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" %
                     (e.response()['message'], e.response()['code']))
        logger.error("fail to power on guest %" % domain_name)
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

    if timeout == 0:
        logger.info("fail to power on vm %s" % domain_name)
        return 1

    return 0

def guest_power_off(domobj, domain_name):
    """ power off guest virtual machine"""

    state = domobj.get_state(domain_name)
    logger.debug("current guest status: %s" %state)
    try:
        domobj.destroy(domain_name)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" %
                     (e.response()['message'], e.response()['code']))
        logger.error("fail to power off guest %" % domain_name)
        return 1

    time.sleep(1)
    state = domobj.get_state(domain_name)
    if state == "shutoff" or state == "shutdown":
        logger.info("the guest is power off already.")
    else:
        logger.error("failed to power off the domain %s" % domain_name)
        return 1

    return 0


def balloon_memory(params):
    """testing balloon memory for guest virtual machine
       Return 0 on SUCCESS or 1 on FAILURE
    """
    # Initiate and check parameters
    global logger
    logger = params['logger']
    params.pop('logger')
    params_check_result = check_params(params)
    if params_check_result:
        return 1
    domain_name = params['guestname']
    memorypair = params['memorypair']
    minmem = int(memorypair.split(',')[0]) * 1024
    logger.info("the minimum memory is %s" % minmem)
    maxmem = int(memorypair.split(',')[1]) * 1024
    logger.info("the maximum memory is %s" % maxmem)

    # Connect to local hypervisor connection URI
    global util
    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')

    logger.info("get the mac address of vm %s" % domain_name)
    mac = util.get_dom_mac_addr(domain_name)
    logger.info("the mac address of vm %s is %s" % (domain_name, mac))

    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)
    domobj = domainAPI.DomainAPI(virconn)

    Defined_dom_list =  domobj.get_defined_list()
    Active_dom_list = domobj.get_list()

    if domain_name not in Defined_dom_list and \
       domain_name not in Active_dom_list:
        logger.error("guest %s doesn't exist" % domain_name)
        return return_close(conn, logger, 1)
    elif domain_name in Defined_dom_list:
        logger.info("guest %s exists but not running , \
                     we begin to set memory to maximum memory" % domain_name)

    elif domain_name in Active_dom_list:
        logger.info("guest %s is running now, \
                     power off it to set memory to maximum memory" %
                     domain_name)
        ret = guest_power_off(domobj, domain_name)
        if ret:
            return return_close(conn, logger, 1)

    # Redefine domain with specified memory size
    newguestxml = redefine_memory_size(domobj, domain_name, maxmem)
    logger.debug('''new guest %s xml :\n%s''' %(domain_name, newguestxml))

    logger.info("undefine the original guest")
    try:
        domobj.undefine(domain_name)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" %
                     (e.response()['message'], e.response()['code']))
        logger.error("fail to undefine guest %" % domain_name)
        return return_close(conn, logger, 1)

    logger.info("define guest with new xml")
    try:
        domobj.define(newguestxml)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" %
                     (e.response()['message'], e.response()['code']))
        logger.error("fail to define guest %s" % domain_name)
        return return_close(conn, logger, 1)

    logger.info("memory set is finished, boot up the guest %s " % domain_name)
    ret = guest_power_on(domobj, domain_name, mac)
    if ret:
        return return_close(conn, logger, 1)

    time.sleep(10)
    ip = util.mac_to_ip(mac, 180)
    current_memory = get_mem_size(ip)

    logger.info("the current memory size is %s" % current_memory)

    logger.info("Now, set the memory size of guest to the minimum value")

    try:
        domobj.set_memory(domain_name, minmem)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" %
                     (e.response()['message'], e.response()['code']))
        logger.error("fail to set memory size")
        return return_close(conn, logger, 1)

    logger.debug("dump the xml description of guest virtual machine %s" %
                  domain_name)
    dom_xml = domobj.get_xml_desc(domain_name)
    logger.debug("the xml definination is %s" % dom_xml)

    count = 0

    current_memory = get_mem_size(ip)

    logger.info("comparing the actual memory size with \
                 expected memory size after balloon operation")
    result = compare_memory(minmem, current_memory)
    if result:
        logger.info("the actual size of memory is \
                     not rounded to the value %s we expected" % minmem)
        count += 1
    else:
        logger.info("the actual size of memory is \
                     rounded to the value %s we expected" % minmem)

    logger.info("Now, we restore back the memory size of \
                 guest to the maximum value")

    try:
        domobj.set_memory(domain_name, maxmem)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" %
                     (e.response()['message'], e.response()['code']))
        logger.error("fail to set memory size")
        return return_close(conn, logger, 1)

    logger.debug("dump the xml description of \
                  guest virtual machine %s" % domain_name)
    dom_xml = domobj.get_xml_desc(domain_name)
    logger.debug("the xml definination is %s" % dom_xml)

    current_memory = get_mem_size(ip)
    logger.info("comparing the actual memory size with \
                 expected memory size after balloon operation")
    result = compare_memory(maxmem, current_memory)
    if result:
        logger.info("the actual size of memory is \
                     not rounded to the value %s we expected" % maxmem)
        count += 1
    else:
        logger.info("the actual size of memory is \
                     rounded to the value %s we expected" % maxmem)

    util.clean_ssh()

    if count:
        return return_close(conn, logger, 1)
    else:
        return return_close(conn, logger, 0)

def balloon_memory_clean(params):
    """ clean testing environment """
    pass
