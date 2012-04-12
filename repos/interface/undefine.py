#!/usr/bin/env python

import os
import re
import sys

import libvirt
from libvirt import libvirtError

from utils import xmlbuilder

required_params = ('ifacename')
optional_params = ()

def check_undefine_interface(ifacename):
    """Check undefining interface result, if undefine interface is successful,
       ifcfg-ifacename will not exist under /etc/sysconfig/network-scripts/
    """
    path = "/etc/sysconfig/network-scripts/ifcfg-%s" % ifacename
    if not os.access(path, os.R_OK):
        return True
    else:
        return False


def undefine(params):
    """Undefine a specific interface"""
    test_result = False
    global logger
    logger = params['logger']
    ifacename = params['ifacename']

    uri = params['uri']

    conn = libvirt.open(uri)

    if check_undefine_interface(ifacename):
        logger.error("interface %s have been undefined" % ifacename)
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    ifaceobj = conn.interfaceLookupByName(ifacename)

    try:
        try:
            ifaceobj.undefine()
            if check_undefine_interface(ifacename):
                logger.info("undefine a interface form xml is successful")
                test_result = True
            else:
                logger.error("fail to check undefine interface")
                test_result = False
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            logger.error("fail to undefine a interface from xml")
            test_result = False
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    if test_result:
        return 0
    else:
        return 1
