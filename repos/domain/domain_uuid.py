#!/usr/bin/env python
"""testing "virsh domuuid" function
"""

import os
import sys
import re
import commands

import libvirt
from libvirt import libvirtError


VIRSH_DOMUUID = "virsh domuuid"

def check_domain_exists(conn, guestname, logger):
    """ check if the domain exists, may or may not be active """
    guest_names = []
    ids = conn.listDomainsID()
    for id in ids:
        obj = conn.lookupByID(id)
        guest_names.append(obj.name())

    guest_names += conn.listDefinedDomains()

    if guestname not in guest_names:
        logger.error("%s doesn't exist" % guestname)
        return False
    else:
        return True

def check_domain_uuid(guestname, UUIDString, logger):
    """ check UUID String of guest """
    status, ret = commands.getstatusoutput(VIRSH_DOMUUID + ' %s' % guestname)
    if status:
        logger.error("executing "+ "\"" +  VIRSH_DOMUUID + ' %s' % guestname + "\"" + " failed")
        logger.error(ret)
        return False
    else:
        UUIDString_virsh = ret[:-1]
        logger.debug("UUIDString from API is %s" % UUIDString)
        logger.debug("UUIDString from virsh domuuid is %s" % UUIDString_virsh)
        if UUIDString == ret[:-1]:
            return True
        else:
            return False

def domuuid(params):
    """check virsh domuuid command
    """
    logger = params['logger']

    if 'guestname' not in params:
        logger.error("option guestname is required")
        return 1
    else:
        guestname = params['guestname']
        logger.info("guest name is %s" % guestname)

    uri = params['uri']
    conn = libvirt.open(uri)

    logger.info("the uri is %s" % uri)

    if not check_domain_exists(conn, guestname, logger):
        logger.error("need a defined guest")
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    domobj = conn.lookupByName(guestname)

    try:
        try:
            logger.info("get the UUID string of %s" % guestname)
            UUIDString = domobj.UUIDString()
            if check_domain_uuid(guestname, UUIDString, logger):
                logger.info("UUIDString from API is the same as the one from virsh")
                logger.info("UUID String is %s" % UUIDString)
                return 0
            else:
                logger.error("UUIDString from API is not the same as the one from virsh")
                return 1
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0
