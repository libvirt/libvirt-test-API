#!/usr/bin/env python
"""for testing the suspend function of domain
   mandatory arguments: guestname
"""

import os
import sys
import re
import time

from lib import connectAPI
from lib import domainAPI
from utils.Python import utils

__author__ = "Osier Yang <jyang@redhat.com>"
__date__ = "Tue Oct 27, 2009"
__version__ = "0.1.0"
__credits__ = "Copyright (C) 2009 Red Hat, Inc."
__all__ = ['suspend',
          'check_params',
          'parse_opts',
          'usage',
          'version']

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

def suspend(params):
    """Suspend domain

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
    conn = connectAPI.ConnectAPI(uri)
    conn.open()

    # Suspend domain
    domobj = domainAPI.DomainAPI(conn)
    logger.info('suspend domain')
    try:
        domobj.suspend(domname)
    except Exception, e:
        logger.error(str(e))
        logger.error("suspend failed")
        return return_close(conn, logger, 1)
    time.sleep(1)
    state = domobj.get_state(domname)

    if state != "paused":
        logger.error('The domain state is not equal to "paused"')
        return return_close(conn, logger, 1)

    mac = util.get_dom_mac_addr(domname)

    time.sleep(3)
    logger.info("get ip by mac address")
    ip = util.mac_to_ip(mac, 10)

    time.sleep(10)

    logger.info('ping guest')
    if util.do_ping(ip, 20):
        logger.error('The guest is still active, IP: ' + str(ip))
        return return_close(conn, logger, 1)

    logger.info('PASS')
    return return_close(conn, logger, 0)

def suspend_clean(params):
    """ clean testing environment """
    pass
