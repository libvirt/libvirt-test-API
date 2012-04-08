#!/usr/bin/evn python
"""this test case is used for testing destroy network"""

import time
import os
import re
import sys

import libvirt
from libvirt import libvirtError

from utils import utils

def usage(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    keys = ['networkname']
    for key in keys:
        if key not in params:
            logger.error("%s is required" %key)
            return 1
        elif len(params[key]) == 0:
            logger.error("%s value is empty, please inputting a value" %key)
            return 1
        else:
            pass

def check_network_status(*args):
    """Check current network status, it will return True if
       current network is active, otherwise, return False
    """
    (networkname, conn, logger) = args

    net_list = conn.listNetworks()
    logger.debug("current active network list:")
    logger.debug(net_list)
    if networkname in net_list:
        return True
    else:
        return False

def destroy(params):
    """destroy network"""
    usage(params)

    logger = params['logger']
    networkname = params['networkname']

    test_result = False

    util = utils.Utils()
    uri = params['uri']

    conn = libvirt.open(uri)

    if not check_network_status(networkname, conn, logger):
        logger.error("the %s network is inactive" % networkname)
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    netobj = conn.networkLookupByName(networkname)
    net_num1 = conn.numOfNetworks()
    logger.info("original network active number: %s" % net_num1)

    try:
        try:
            netobj.destroy()
            net_num2 = conn.numOfNetworks()
            if not check_network_status(networkname, conn, logger) and \
                net_num1 > net_num2:
                logger.info("current network active number: %s\n" % net_num2)
                logger.info("destroy %s network successful" % networkname)
            else:
                logger.error("the %s network is still running" % networkname)
                return 1
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            logger.error("fail to destroy %s network" % networkname)
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    time.sleep(3)
    return 0
