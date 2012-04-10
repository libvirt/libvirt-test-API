#!/usr/bin/env python
"""this test case is used for testing attach
   the interface to domain from xml
   mandatory arguments:guestname
                       ifacetype
                       source
   optional arguments: hdmodel
"""

import os
import re
import sys

import libvirt
from libvirt import libvirtError

from utils import utils
from utils import xmlbuilder

def usage(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    keys = ['guestname', 'ifacetype', 'source']
    optional_keys = ['hdmodel']
    for key in keys:
        if key not in params:
            logger.error("%s is required" %key)
            return 1

def check_guest_status(guestname, domobj):
    """Check guest current status"""
    state = domobj.get_state(guestname)
    if state == "shutoff" or state == "shutdown":
    # add check function
        return False
    else:
        return True

def check_attach_interface(num1, num2):
    """Check attach interface result via simple interface number comparison """
    if num2 > num1:
        return True
    else:
        return False

def attach_interface(params):
    """Attach a interface to domain from xml"""
    # Initiate and check parameters
    usage(params)
    logger = params['logger']
    guestname = params['guestname']
    test_result = False

    # Connect to local hypervisor connection URI
    uri = params['uri']
    conn = libvirt.open(uri)

    domobj = conn.lookupByName(guestname)

    # Generate interface xml
    xmlobj = xmlbuilder.XmlBuilder()
    interfacexml = xmlobj.build_interface(params)
    logger.debug("interface xml:\n%s" %interfacexml)

    iface_num1 = utils.dev_num(guestname, "interface")
    logger.debug("original interface number: %s" %iface_num1)

    # Attach interface to domain
    try:
        try:
            domobj.attachDeviceFlags(interfacexml, 0)
            iface_num2 = utils.dev_num(guestname, "interface")
            logger.debug("update interface number to %s" %iface_num2)
            if  check_attach_interface(iface_num1, iface_num2):
                logger.info("current interface number: %s" %iface_num2)
                test_result = True
            else:
                logger.error("fail to attach a interface to guest: %s" %iface_num2)
                test_result = False
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            logger.error("attach a interface to guest %s" % guestname)
            test_result = False
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    if test_result:
        return 0
    else:
        return 1
