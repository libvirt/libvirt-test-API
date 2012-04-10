#!/usr/bin/env python
"""this test case is used for testing detach
   the interface to domain from xml
   mandatory arguments: guestname
                        ifacetype
                        source
                        nicmodel
"""

import os
import re
import sys
import time

import libvirt
from libvirt import libvirtError

from utils import utils
from utils import xmlbuilder

def usage(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    keys = ['guestname', 'ifacetype', 'source', 'nicmodel']
    for key in keys:
        if key not in params:
            logger.error("%s is required" %key)
            return 1

def check_guest_status(domobj):
    """Check guest current status"""
    state = domobj.info()[0]
    if state == libvirt.VIR_DOMAIN_SHUTOFF or state == libvirt.VIR_DOMAIN_SHUTDOWN:
    # add check function
        return False
    else:
        return True

def check_detach_interface(num1, num2):
    """Check detach interface result via simple interface number
       comparison
    """
    if num2 < num1:
        return True
    else:
        return False

def detach_interface(params):
    """Detach a interface to domain from xml"""
    # Initiate and check parameters
    usage(params)
    logger = params['logger']
    guestname = params['guestname']
    test_result = False

    # Connect to local hypervisor connection URI
    uri = params['uri']
    macs = utils.get_dom_mac_addr(guestname)
    mac_list = macs.split("\n")
    logger.debug("mac address: \n%s" % macs)
    params['macaddr'] = mac_list[-1]

    conn = libvirt.open(uri)
    domobj = conn.lookupByName(guestname)

    xmlobj = xmlbuilder.XmlBuilder()
    ifacexml = xmlobj.build_interface(params)
    logger.debug("interface xml:\n%s" % ifacexml)

    iface_num1 = utils.dev_num(guestname, "interface")
    logger.debug("original interface number: %s" % iface_num1)

    if check_guest_status(domobj):
        pass
    else:
        domobj.create()
        time.sleep(90)

    try:
        try:
            domobj.detachDevice(ifacexml)
            iface_num2 = utils.dev_num(guestname, "interface")
            logger.debug("update interface number to %s" % iface_num2)
            if  check_detach_interface(iface_num1, iface_num2):
                logger.info("current interface number: %s" % iface_num2)
                test_result = True
            else:
                logger.error("fail to detach a interface to guest: %s" %
                              iface_num2)
                test_result = False
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            logger.error("detach the interface from guest %s" % guestname)
            test_result = False
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    if test_result:
        return 0
    else:
        return -1
