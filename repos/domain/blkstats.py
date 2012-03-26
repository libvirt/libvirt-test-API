#!/usr/bin/evn python
"""this test case is used for testing domain block
   device statistics
   mandatory arguments: guestname
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Wed Jan 27, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_guest_status', 'check_blkstats',
           'blkstats']

import os
import sys
import time

dir = os.path.dirname(sys.modules[__name__].__file__)
absdir = os.path.abspath(dir)
rootdir = os.path.split(os.path.split(absdir)[0])[0]
sys.path.append(rootdir)

import exception
from lib import connectAPI
from lib import domainAPI
from utils.Python import utils

def usage(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    keys = ['guestname']
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

def check_blkstats():
    """Check block device statistic result"""
    pass

def blkstats(params):
    """Domain block device statistic"""
    # Initiate and check parameters
    usage(params)
    logger = params['logger']
    guestname = params['guestname']
    test_result = False

    # Connect to local hypervisor connection URI
    util = utils.Utils()
    uri = params['uri']
    conn = connectAPI.ConnectAPI(uri)
    conn.open()

    caps = conn.get_caps()
    logger.debug(caps)

    # Check domain block status
    domobj = domainAPI.DomainAPI(conn)
    if check_guest_status(guestname, domobj):
        pass
    else:
        domobj.start(guestname)
        time.sleep(90)
    try:
        try:
            (blkstats, path) = domobj.get_block_stats(guestname)
        except exception.LibvirtAPI, e:
            logger.error("libvirt error: error code - %s; error message - %s" %(e.code, e.message))
            return 1;
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    if blkstats:
        # check_blkstats()
        logger.debug(blkstats)
        logger.info("%s rd_req %s" %(path, blkstats[0]))
        logger.info("%s rd_bytes %s" %(path, blkstats[1]))
        logger.info("%s wr_req %s" %(path, blkstats[2]))
        logger.info("%s wr_bytes %s" %(path, blkstats[3]))
        test_result = True
    else:
        logger.error("fail to get domain block statistics\n")
        test_result = False

    if test_result:
        return 0
    else:
        return 1

def blkstats_clean(params):
    """ clean testing environment """
    pass
