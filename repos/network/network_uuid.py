#!/usr/bin/env python
# To test "virsh net-uuid" command

import os
import sys
import re
import commands

import libvirt
from libvirt import libvirtError

import sharedmod

required_params = ('networkname',)
optional_params = ()

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
    networkname = params['networkname']

    conn = sharedmod.libvirtobj['conn']

    if not check_network_exists(conn, networkname, logger):
        logger.error("need a defined network")
        return 1

    netobj = conn.networkLookupByName(networkname)

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

    return 0
