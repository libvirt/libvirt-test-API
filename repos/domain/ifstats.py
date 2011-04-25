#!/usr/bin/evn python
"""this test case is used for testing domain interface
   statistics
   mandatory arguments: guestname
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Wed Jan 27, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_guest_status', 'check_interface_stats',
           'interface_stats']

import os
import re
import sys
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

from lib import connectAPI
from lib import domainAPI
from utils.Python import utils
from exception import LibvirtAPI

def usage(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    keys = ['guestname']
    for key in keys:
        if key not in params:
            logger.error("%s is required" % key)
            return 1

def check_guest_status(guestname, domobj):
    """Check guest current status"""
    state = domobj.get_state(guestname)
    if state == "shutoff" or state == "shutdown":
    # add check function
        return False
    else:
        return True

def check_interface_stats():
    """Check interface statistic result"""
    pass

def interface_stats(params):
    """Domain interface statistic"""
    usage(params)

    logger = params['logger']
    guestname = params['guestname']
    test_result = False

    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')

    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    caps = conn.get_caps()
    logger.debug(caps)

    domobj = domainAPI.DomainAPI(virconn)

    if check_guest_status(guestname, domobj):
        pass
    else:
        try:
            logger.info("%s is not running , power on it" % guestname)
            domobj.start(guestname)
        except LibvirtAPI, e:
            logger.error(str(e))
            logger.error("start failed")
            conn.close()
            logger.info("closed hypervisor connection")       
            return 1
        
    mac = util.get_dom_mac_addr(guestname)
    logger.info("get ip by mac address")
    ip = util.mac_to_ip(mac, 180)

    logger.info('ping guest')
    if not util.do_ping(ip, 300):
        logger.error('Failed on ping guest, IP: ' + str(ip))
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    (ifstats, path) = domobj.get_interface_stats(guestname)
    if ifstats:
    # check_interface_stats()
        logger.debug(ifstats)
        logger.info("%s rx_bytes %s" % (path, ifstats[0]))
        logger.info("%s rx_packets %s" % (path, ifstats[1]))
        logger.info("%s rx_errs %s" % (path, ifstats[2]))
        logger.info("%s rx_drop %s" % (path, ifstats[3]))
        logger.info("%s tx_bytes %s" % (path, ifstats[4]))
        logger.info("%s tx_packets %s" % (path, ifstats[5]))
        logger.info("%s tx_errs %s" % (path, ifstats[6]))
        logger.info("%s tx_drop %s" % (path, ifstats[7]))
        test_result = True
    else:
        logger.error("fail to get domain interface statistics\n")
        test_result = False
   
    conn.close()
    logger.info("closed hypervisor connection")

    if test_result:
        return 0
    else:
        return -1

def interface_stats_clean(params):
    """ clean testing environment """
    pass
