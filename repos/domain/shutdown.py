#!/usr/bin/env python
"""for testing the shutdown function of domain
   mandatory arguments: guestname
"""

import os
import sys
import re
import time

import libvirt
from libvirt import libvirtError

from utils.Python import utils

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

def shutdown(params):
    """Shutdown domain

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
    conn = libvirt.open(uri)
    domobj = conn.lookupByName(domname)

    timeout = 600
    logger.info('shutdown domain')
    mac = util.get_dom_mac_addr(domname)
    logger.info("get ip by mac address")
    ip = util.mac_to_ip(mac, 180)
    logger.info("the ip address of guest is %s" % ip)

    # Shutdown domain
    try:
        domobj.shutdown()
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        logger.error("shutdown failed")
        return return_close(conn, logger, 1)

    # Check domain status by ping ip
    while timeout:
        time.sleep(10)
        timeout -= 10
        logger.info(str(timeout) + "s left")

        state = domobj.info()[0]
        if state == libvirt.VIR_DOMAIN_SHUTOFF:
            break

    if timeout <= 0:
        logger.error('The domain state is not equal to "shutoff"')
        return return_close(conn, logger, 1)

    logger.info('ping guest')
    if util.do_ping(ip, 300):
        logger.error('The guest is still active, IP: ' + str(ip))
        return return_close(conn, logger, 1)
    else:
        logger.info("domain %s shutdown successfully" % domname)

    return return_close(conn, logger, 0)

def shutdown_clean(params):
    """ clean the testing environment """
    pass
