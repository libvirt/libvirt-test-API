#!/usr/bin/env python
# To test "virsh net-name" command

import os
import sys
import re
import commands

import libvirt
from libvirt import libvirtError

import sharedmod

required_params = ('networkname',)
optional_params = ()

VIRSH_NETNAME = "virsh net-name"

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
    """ check the output of virsh net-name """
    status, ret = commands.getstatusoutput(VIRSH_NETNAME + ' %s' % UUIDString)
    if status:
        logger.error("executing "+ "\"" +  VIRSH_NETNAME + ' %s' % UUIDString + "\"" + " failed")
        logger.error(ret)
        return False
    else:
        networkname_virsh = ret[:-1]
        logger.debug("networkname from " + VIRSH_NETNAME + " is %s" % networkname_virsh)
        logger.debug("networkname we expected is %s" % networkname)
        if networkname_virsh == networkname:
            return True
        else:
            return False

def netname(params):
    """ get the UUIDString of a network, then call
        virsh net-name to generate the name of network,
        then check it
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
            logger.info(VIRSH_NETNAME + " test succeeded.")
            return 0
        else:
            logger.error(VIRSH_NETNAME + " test failed.")
            return 1
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        return 1

    return 0
