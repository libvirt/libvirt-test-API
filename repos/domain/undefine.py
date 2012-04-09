#!/usr/bin/evn python

import os
import re
import sys

import libvirt
from libvirt import libvirtError


def check_undefine_domain(guestname):
    """Check undefine domain result, if undefine domain is successful,
       guestname.xml will don't exist under /etc/libvirt/qemu/
    """
    path = "/etc/libvirt/qemu/%s.xml" % guestname
    if not os.access(path, os.R_OK):
        return True
    else:
        return False

def undefine(params):
    """Undefine a domain"""
    # Initiate and check parameters
    usage(params)
    logger = params['logger']
    guestname = params['guestname']
    test_result = False

    # Connect to local hypervisor connection URI
    uri = params['uri']
    conn = libvirt.open(uri)

    domobj = conn.lookupByName(guestname)

    try:
        try:
            domobj.undefine()
            if check_undefine_domain(guestname):
                logger.info("undefine the domain is successful")
                test_result = True
            else:
                logger.error("fail to check domain undefine")
                test_result = False
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            test_result = False
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    if test_result:
        return 0
    else:
        return 1

def undefine_clean(params):
    """ clean testing environment """
    pass
