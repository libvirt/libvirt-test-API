#!/usr/bin/env python
"""for testing the resume function of domain
   mandatory arguments: guestname
"""

__author__ = "Osier Yang <jyang@redhat.com>"
__date__ = "Tue Oct 27, 2009"
__version__ = "0.1.0"
__credits__ = "Copyright (C) 2009 Red Hat, Inc."
__all__ = ['resume',
          'check_params',
          'parse_opts',
          'usage',
          'version',
          'append_path']

import os
import sys
import re

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
from lib import domainAPI
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
    uri = util.get_uri('127.0.0.1')

    # Resume domain
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)
    domobj = domainAPI.DomainAPI(virconn)
    logger.info('resume domain')
    try:
        domobj.resume(domname)
    except Exception, e:
        logger.error(str(e))
        logger.error("resume failed")
        return return_close(conn, logger, 1)

    state = domobj.get_state(domname)
    expect_states = ['running', 'no state', 'blocked']

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
