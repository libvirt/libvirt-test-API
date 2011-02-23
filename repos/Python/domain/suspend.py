#!/usr/bin/env python
"""for testing the suspend function of domain
   mandatory arguments: guestname
"""

import os
import sys
import re
import time

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
from lib.Python import domainAPI
from utils.Python import utils

__author__ = "Osier Yang <jyang@redhat.com>"
__date__ = "Tue Oct 27, 2009"
__version__ = "0.1.0"
__credits__ = "Copyright (C) 2009 Red Hat, Inc."
__all__ = ['suspend', 
          'check_params',  
          'parse_opts', 
          'usage', 
          'version', 
          'append_path']

def return_fail(logger):
    logger.error("FAIL")
    return 1

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
    uri = util.get_uri('127.0.0.1')
    virconn = connectAPI.ConnectAPI().open(uri)
    
    # Suspend domain 
    domobj = domainAPI.DomainAPI(virconn)
    logger.info('suspend domain')
    try:
        domobj.suspend(domname)
    except Exception, e:
        logger.error(str(e))
        return return_fail(logger)
    time.sleep(1)
    state = domobj.get_state(domname)

    if state != "paused":
        logger.error('The domain state is not equal to "paused"')
        return return_fail(logger)

    mac = util.get_dom_mac_addr(domname)

    time.sleep(3)
    logger.info("get ip by mac address")
    ip = util.mac_to_ip(mac, 10)

    time.sleep(10)

    logger.info('ping guest')
    if util.do_ping(ip, 20):
        logger.error('The guest is still active, IP: ' + str(ip))
        return return_fail(logger)

    is_fail = False
    logger.info('PASS')
    return is_fail

