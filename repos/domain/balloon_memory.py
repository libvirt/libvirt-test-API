#!/usr/bin/env python
# To test domain memory ballooning

import os
import sys
import re
import time
import math
from xml.dom import minidom

import libvirt
from libvirt import libvirtError

from utils import utils
from utils import check

required_params = ('guestname', 'memorypair')
optional_params = ()

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

def redefine_memory_size(domobj, domname, memsize):
    """ dump domain xml description to change the memory size,
        then, define the domain again
    """
    guestxml = domobj.XMLDesc(0)
    logger.debug('''original guest %s xml :\n%s''' % (domname, guestxml))

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

def guest_power_on(domobj, domname, mac):
    """ power on guest virtual machine"""

    try:
        domobj.create()
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        logger.error("fail to power on guest %" % domname)
        return 1

    timeout = 600

    while timeout:
        time.sleep(10)
        timeout -= 10

        ip = utils.mac_to_ip(mac, 180)

        if not ip:
            logger.info(str(timeout) + "s left")
        else:
            logger.info("vm %s power on successfully" % domname)
            logger.info("the ip address of vm %s is %s" % (domname, ip))
            break

    if timeout == 0:
        logger.info("fail to power on vm %s" % domname)
        return 1

    return 0

def guest_power_off(domobj, domname):
    """ power off guest virtual machine"""

    state = domobj.info()[0]
    logger.debug("current guest status: %s" %state)
    try:
        domobj.destroy()
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        logger.error("fail to power off guest %" % domname)
        return 1

    time.sleep(1)
    state = domobj.info()[0]
    if state == libvirt.VIR_DOMAIN_SHUTOFF or state == libvirt.VIR_DOMAIN_SHUTDOWN:
        logger.info("the guest is power off already.")
    else:
        logger.error("failed to power off the domain %s" % domname)
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
    domname = params['guestname']
    memorypair = params['memorypair']
    minmem = int(memorypair.split(',')[0]) * 1024
    logger.info("the minimum memory is %s" % minmem)
    maxmem = int(memorypair.split(',')[1]) * 1024
    logger.info("the maximum memory is %s" % maxmem)

    # Connect to local hypervisor connection URI
    global util
    uri = params['uri']

    logger.info("get the mac address of vm %s" % domname)
    mac = utils.get_dom_mac_addr(domname)
    logger.info("the mac address of vm %s is %s" % (domname, mac))

    conn = libvirt.open(uri)

    Defined_dom_list = conn.listDefinedDomains()

    Active_dom_list = []
    ids = conn.listDomainsID()
    for id in ids:
        obj = conn.lookupByID(id)
        Active_dom_list.append(obj.name())

    if domname not in Defined_dom_list and \
       domname not in Active_dom_list:
        logger.error("guest %s doesn't exist" % domname)
        return return_close(conn, logger, 1)
    elif domname in Defined_dom_list:
        logger.info("guest %s exists but not running , \
                     we begin to set memory to maximum memory" % domname)

    elif domname in Active_dom_list:
        logger.info("guest %s is running now, \
                     power off it to set memory to maximum memory" %
                     domname)
        domobj = conn.lookupByName(domname)
        ret = guest_power_off(domobj, domname)
        if ret:
            return return_close(conn, logger, 1)

    # Redefine domain with specified memory size
    newguestxml = redefine_memory_size(domobj, domname, maxmem)
    logger.debug('''new guest %s xml :\n%s''' %(domname, newguestxml))

    logger.info("undefine the original guest")
    try:
        domobj.undefine()
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        logger.error("fail to undefine guest %" % domname)
        return return_close(conn, logger, 1)

    logger.info("define guest with new xml")
    try:
        conn.defineXML(newguestxml)
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        logger.error("fail to define guest %s" % domname)
        return return_close(conn, logger, 1)

    logger.info("memory set is finished, boot up the guest %s " % domname)
    ret = guest_power_on(domobj, domname, mac)
    if ret:
        return return_close(conn, logger, 1)

    time.sleep(10)
    ip = utils.mac_to_ip(mac, 180)
    current_memory = get_mem_size(ip)

    logger.info("the current memory size is %s" % current_memory)

    logger.info("Now, set the memory size of guest to the minimum value")

    try:
        domobj.setMemory(minmem)
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        logger.error("fail to set memory size")
        return return_close(conn, logger, 1)

    logger.debug("dump the xml description of guest virtual machine %s" %
                  domname)
    dom_xml = domobj.XMLDesc(0)
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
        domobj.setMemory(maxmem)
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        logger.error("fail to set memory size")
        return return_close(conn, logger, 1)

    logger.debug("dump the xml description of \
                  guest virtual machine %s" % domname)
    dom_xml = domobj.XMLDesc(0)
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
    if count:
        return return_close(conn, logger, 1)
    else:
        return return_close(conn, logger, 0)

def balloon_memory_clean(params):
    """ clean testing environment """
    pass
