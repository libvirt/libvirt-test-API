#!/usr/bin/env python
"""for testing the resume function of domain
   mandatory arguments: guestname
"""

import os
import sys
import re

import libvirt
from libvirt import libvirtError

from utils import utils

def return_close(conn, logger, ret):
    conn.close()
    logger.info("closed hypervisor connection")
    return ret

def check_params(params):
    """Verify the input parameter"""
    if 'logger' not in params:
        print "key 'logger' is required, and it's value should \
               be an instance of logging.Logger"
        return 1

    logger = params['logger']

    keys = ['guestname', 'logger']
    for key in keys:
        if key not in params:
            logger.error("key '%s' is required" % key)
            usage()

    if params['guestname'] == "":
        logger.error("value of guestname is empty")
        usage()

def resume(params):
    """Resume domain

        Argument is a dictionary with two keys:
        {'logger': logger, 'guestname': guestname}

        logger -- an object of utils/Python/log.py
        guestname -- same as the domain name

        Return 0 on SUCCESS or 1 on FAILURE
    """
    # Initiate and check parameters
    is_fail = True
    check_params(params)
    domname = params['guestname']
    logger = params['logger']

    # Connect to local hypervisor connection URI
    util = utils.Utils()
    uri = params['uri']

    # Resume domain
    conn = libvirt.open(uri)
    domobj = conn.lookupByName(domname)
    logger.info('resume domain')
    try:
        domobj.resume()
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        logger.error("resume failed")
        return return_close(conn, logger, 1)

    state = domobj.info()[0]
    expect_states = [libvirt.VIR_DOMAIN_RUNNING, libvirt.VIR_DOMAIN_NOSTATE, libvirt.VIR_DOMAIN_BLOCKED]

    if state not in expect_states:
        logger.error('The domain state is not equal to "paused"')
        return return_close(conn, logger, 1)

    mac = util.get_dom_mac_addr(domname)
    logger.info("get ip by mac address")
    ip = util.mac_to_ip(mac, 120)

    logger.info('ping guest')
    if not util.do_ping(ip, 300):
        logger.error('Failed on ping guest, IP: ' + str(ip))
        return return_close(conn, logger, 1)

    logger.info("PASS")
    return return_close(conn, logger, 0)

def resume_clean(params):
    """ clean testing environment """
    pass
