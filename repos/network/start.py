#!/usr/bin/evn python
"""this test case is used for testing to activate
   a virtual network
"""

import time
import os
import re
import sys
import commands

import libvirt
from libvirt import libvirtError

from utils import utils

def return_close(conn, logger, ret):
    conn.close()
    logger.info("closed hypervisor connection")
    return ret

def check_params(params):
    """Verify inputing parameter dictionary"""

    keys = ['networkname']
    for key in keys:
        if key not in params:
            logger.error("Argument %s is required" %key)
            return 1

def start(params):
    """activate a defined network"""

    global logger
    logger = params['logger']

    params.pop('logger')

    params_check_result = check_params(params)

    if params_check_result:
        return 1

    networkname = params['networkname']
    logger.info("the name of virtual network to be activated is %s" % \
                 networkname)

    uri = params['uri']

    logger.info("uri address is %s" % uri)

    conn = libvirt.open(uri)

    net_defined_list = conn.listDefinedNetworks()

    if networkname not in net_defined_list:
        logger.error("virtual network %s doesn't exist \
                      or is active already." % networkname)
        return return_close(conn, logger, 1)
    else:
        netobj = conn.networkLookupByName(networkname)
        netxmldesc = netobj.XMLDesc(0)
        logger.debug("the xml description of the virtual network is %s" % \
                      netxmldesc)

    try:
        logger.info("begin to activate virtual network %s" % networkname)
        netobj.create()
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        logger.error("fail to destroy domain")
        return return_close(conn, logger, 1)

    net_activated_list = conn.listNetworks()

    if networkname not in net_activated_list:
        logger.error("virtual network %s failed to be activated." % networkname)
        return return_close(conn, logger, 1)
    else:
        shell_cmd = "virsh net-list --all"
        (status, text) = commands.getstatusoutput(shell_cmd)
        logger.debug("the output of 'virsh net-list --all' is %s" % text)

    logger.info("activate the virtual network successfully.")
    time.sleep(3)

    return return_close(conn, logger, 0)
