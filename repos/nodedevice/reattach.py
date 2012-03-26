#!/usr/bin/env python
"""this test case is used for testing
   reattach a specific node device
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Tue Apr 6, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_node_reattach', 'reattach']


import os
import re
import sys
import commands

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
from lib import nodedevAPI
from utils.Python import utils
from exception import LibvirtAPI


def usage(params):
    """Verify inputing parameter dictionary"""
    keys = ['pciaddress']
    for key in keys:
        if key not in params:
            logger.error("%s is required" %key)
            return 1
        elif len(params[key]) == 0:
            logger.error("%s value is empty, please inputting a value" %key)
            return 1
        else:
            pass

def check_node_reattach(pciaddress):
    """Check node device reattach result, if reattachment is successful, the
       device will be removed from pci-stub driver and return original driver
       to the device, argument 'address' is a address of the node device
    """
    driver_cmd = "readlink /sys/bus/pci/devices/0000:%s/driver/ -f" % pciaddress
    logger.debug("execute shell cmd line: %s " % driver_cmd)
    (status, retval) = commands.getstatusoutput(driver_cmd)
    if status != 0:
        logger.error("shell cmd line exit status: %d" % status)
        logger.error("shell cmd line exit result: %s" % retval)
        return 1
    else:
        logger.debug("shell cmd line exit status: %d" % status)

    driver = os.path.basename(retval)
    return driver

def reattach(dicts):
    """Reattach a specific node device and removed it
       from pci-stub driver, argument 'dicts' is a dictionary type
       and includes 'pciaddress' key, whose value
       uniquely identify a pci address of the node device
    """
    usage(dicts)

    test_result = False
    global logger

    logger = dicts['logger']
    pciaddress = dicts['pciaddress']

    original_driver = check_node_reattach(pciaddress)
    logger.info("original device driver: %s" % original_driver)

    util = utils.Utils()
    uri = params['uri']

    kernel_version = util.get_host_kernel_version()
    hypervisor = util.get_hypervisor()
    pciback = ''
    if hypervisor == 'kvm':
        pciback = 'pci-stub'
    if hypervisor == 'xen':
        pciback = 'pciback'

    if 'el5' in kernel_version:
        vendor_product_get = "lspci -n |grep %s|awk '{print $3}'" % pciaddress
        logger.debug("the vendor:product is %s" % vendor_product_get)
        (status, retval) = commands.getstatusoutput(vendor_product_get)
        if status != 0:
            logger.error("failed to get vendor product ID")
            return 1
        else:
            vendor_ID = retval.split(":")[0]
            product_ID = retval.split(":")[1]
            device_name = "pci_%s_%s" % (vendor_ID, product_ID)
    elif 'el6' in kernel_version:
        (bus, slot_func) = pciaddress.split(":")
        (slot, func) = slot_func.split(".")
        device_name = "pci_0000_%s_%s_%s" % (bus, slot, func)

    logger.debug("the name of the pci device is: %s" % device_name)

    conn = connectAPI.ConnectAPI(uri)
    conn.open()

    caps = conn.get_caps()
    logger.debug(caps)

    nodeobj = nodedevAPI.NodedevAPI(conn)

    try:
        try:
            nodeobj.reattach(device_name)
            logger.info("reattach the node device")
            current_driver = check_node_reattach(pciaddress)
            logger.info("current device driver: %s" % current_driver)
            if original_driver == pciback and current_driver != pciback:
                logger.info("the node %s device reattach is successful" \
                            % device_name)
                test_result = True
            else:
                logger.info("the node %s device reattach is failed" % device_name)
                test_result = False
                return 1
        except LibvirtAPI, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.response()['message'], e.response()['code']))
            logger.error("Error: fail to reattach %s node device" % device_name)
            test_result = False
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    if test_result:
        return 0
    else:
        return 1
