#!/usr/bin/evn python
"""this test case is used for testing domain block
   device statistics
   mandatory arguments: guestname
"""

import os
import sys
import time
import libxml2

import libvirt
from libvirt import libvirtError

from utils.Python import utils

def usage(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    keys = ['guestname']
    for key in keys:
        if key not in params:
            logger.error("%s is required" %key)
            return 1

def check_guest_status(domobj):
    """Check guest current status"""
    state = domobj.info()[0]
    if state == libvirt.VIR_DOMAIN_SHUTOFF or state == libvirt.VIR_DOMAIN_SHUTDOWN:
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
    conn = libvirt.open(uri)

    domobj = conn.lookupByName(guestname)

    # Check domain block status
    if check_guest_status(domobj):
        pass
    else:
        domobj.create()
        time.sleep(90)
    try:
        try:
            xml = domobj.XMLDesc(0)
            doc = libxml2.parseDoc(xml)
            cont = doc.xpathNewContext()
            devs = cont.xpathEval("/domain/devices/disk/target/@dev")
            path = devs[0].content
            blkstats = domobj.blockStats(path)
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
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
