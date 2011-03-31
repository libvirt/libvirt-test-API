#!/usr/bin/env python
"""this test case is used for testing
   restore domain from a disk save image
   mandatory arguments: guestname
                        filepath
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Wed Mar 24, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'get_guest_ipaddr', 'restore',
           'check_guest_status', 'check_guest_restore']

import os
import re
import sys

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
from exception import LibvirtAPI

def return_close(conn, logger, ret):
    conn.close()
    logger.info("closed hypervisor connection")
    return ret

def usage(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    keys = ['guestname', 'filepath' ]
    for key in keys:
        if key not in params:
            logger.error("%s is required" % key)
            return 1
        elif len(params[key]) == 0:
            logger.error("%s value is empty, please inputting a value" % key)
            return 1
        else:
            pass

def get_guest_ipaddr(*args):
    """Get guest ip address"""
    (guestname, util, logger) = args

    mac = util.get_dom_mac_addr(guestname)
    logger.debug("guest mac address: %s" % mac)

    ipaddr = util.mac_to_ip(mac, 15)
    logger.debug("guest ip address: %s" % ipaddr)

    if util.do_ping(ipaddr, 20) == 1:
        logger.info("ping current guest successfull")
        return ipaddr
    else:
        logger.error("Error: can't ping current guest")
        return None

def check_guest_status(*args):
    """Check guest current status"""
    (guestname, domobj, logger) = args

    state = domobj.get_state(guestname)
    logger.debug("current guest status: %s" % state)

    if state == "shutoff" or state == "shutdown":
        return False
    else:
        return True

def check_guest_restore(*args):
    """Check restore domain result, if restore domain is successful,
       guest status will not be paused and can be ping
    """
    (guestname, domobj, util, logger) = args

    if check_guest_status(guestname, domobj, logger):
        if get_guest_ipaddr(guestname, util, logger):
            return True
        else:
            return False
    else:
        return False

def restore(params):
    """Save domain to a disk file"""
    # Initiate and check parameters
    usage(params)
    logger = params['logger']
    guestname = params['guestname']
    filepath = params['filepath']
    test_result = False

    # Connect to local hypervisor connection URI
    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    caps = conn.get_caps()
    logger.debug(caps)

    # Restore domain
    domobj = domainAPI.DomainAPI(virconn)
    if check_guest_status(guestname, domobj, logger):
        logger.error("Error: current guest status is not shutoff or shutdown,\
                      can not do restore operation")
        return return_close(conn, logger, 1)

    try:
        domobj.restore(guestname, filepath)
        if check_guest_restore(guestname, domobj, util, logger):
            logger.info("restore %s domain successful" % guestname)
            test_result = True
        else:
            logger.error("Error: fail to check restore domain")
            test_result = False
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" %
                      (e.response()['message'], e.response()['code']))
        logger.error("Error: fail to restore %s domain" % guestname)
        test_result = False

    if test_result:
        return return_close(conn, logger, 0)
    else:
        return return_close(conn, logger, 1)
