#!/usr/bin/env python
"""testing "virsh net-uuid" function
"""

import os
import sys
import re
import commands

import libvirt
from libvirt import libvirtError

from utils import utils

VIRSH_NETUUID = "virsh net-uuid"

def check_network_exists(conn, networkname, logger):
    """ check if the network exists, may or may not be active """
    network_names = conn.listNetworks()
    network_names += conn.listDefinedNetworks()

    if networkname not in network_names:
        logger.error("%s doesn't exist" % networkname)
        return False
    else:
        return True

def check_network_uuid(networkname, UUIDString, logger):
    """ check UUID String of a network """
    status, ret = commands.getstatusoutput(VIRSH_NETUUID + ' %s' % networkname)
    if status:
        logger.error("executing "+ "\"" +  VIRSH_NETUUID + ' %s' % networkname + "\"" + " failed")
        logger.error(ret)
        return False
    else:
        UUIDString_virsh = ret[:-1]
        logger.debug("UUIDString from API is %s" % UUIDString)
        logger.debug("UUIDString from " + "\"" + VIRSH_NETUUID + "\"" " is %s" % UUIDString_virsh)
        if UUIDString_virsh == UUIDString:
            return True
        else:
            return False

def netuuid(params):
    """ call appropriate API to generate the UUIDStirng
        of a network , then compared to the output of command
        virsh net-uuid
    """
    logger = params['logger']
    if 'networkname' not in params:
        logger.error("the option networkname is required")
        return 1
    else:
        networkname = params['networkname']

    util = utils.Utils()
    uri = params['uri']
    conn = libvirt.open(uri)

    logger.info("the uri is %s" % uri)

    if not check_network_exists(conn, networkname, logger):
        logger.error("need a defined network")
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    netobj = conn.networkLookupByName(networkname)

    try:
        try:
            UUIDString = netobj.UUIDString()
            logger.info("the UUID string of network %s is %s" % (networkname, UUIDString))

            if check_network_uuid(networkname, UUIDString, logger):
                logger.info(VIRSH_NETUUID + " test succeeded.")
                return 0
            else:
                logger.error(VIRSH_NETUUID + " test failed.")
                return 1
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0
