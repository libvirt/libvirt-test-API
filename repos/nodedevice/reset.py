#!/usr/bin/env python
"""this test case is used for testing
   reset a specific node device
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Tue Apr 6, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_node_reset', 'reset']

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

from lib.Python import connectAPI
from lib.Python import nodedevAPI
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

def check_node_reset():
    """Check node device reset result, I have no idea how to check it now"""
    pass

def reset(dicts):
    """Reset a specific node device and return clean & certain status to it"""
    usage(dicts)

    test_result = False
    global logger

    logger = dicts['logger']
    pciaddress = dicts['pciaddress']

    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')

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
    elif 'el6' in kernel_version:
        (bus, slot_func) = pciaddress.split(":")
        (slot, func) = slot_func.split(".")
        device_name = "pci_0000_%s_%s_%s" % (bus, slot, func)

    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    caps = conn.get_caps()
    logger.debug(caps)

    nodeobj = nodedevAPI.NodedevAPI(virconn)

    try:
        nodeobj.reset(device_name)
        logger.info("reset the node device")
        logger.info("the node %s device reset is successful" % device_name)
        test_result = True
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.response()['message'], e.response()['code']))
        logger.error("Error: fail to reset %s node device" % device_name)
        test_result = False
        return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    if test_result:
        return 0
    else:
        return 1
