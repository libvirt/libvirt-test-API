#!/usr/bin/env python
"""this test case is used for testing
   reset a specific node device
"""

import os
import re
import sys
import commands

import libvirt
from libvirt import libvirtError

from utils.Python import utils

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

def check_node_reset():
    """Check node device reset result, I have no idea how to check it now"""
    pass

def reset(params):
    """Reset a specific node device and return clean & certain status to it"""
    usage(params)

    global logger

    logger = params['logger']
    pciaddress = params['pciaddress']

    util = utils.Utils()
    uri = params['uri']

    kernel_version = util.get_host_kernel_version()

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
    else:
        (bus, slot_func) = pciaddress.split(":")
        (slot, func) = slot_func.split(".")
        device_name = "pci_0000_%s_%s_%s" % (bus, slot, func)

    conn = libvirt.open(uri)

    try:
        try:
            nodeobj = conn.nodeDeviceLookupByName(device_name)
            nodeobj.reset()
            logger.info("reset the node device")
            logger.info("the node %s device reset is successful" % device_name)
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            logger.error("Error: fail to reset %s node device" % device_name)
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0
