#!/usr/bin/env python
""""virsh snapshot-revert" testing
   mandatory arguments: guestname snapshotname
"""

import os
import sys
import re

import libvirt
from libvirt import libvirtError

from utils.Python import utils

def check_params(params):
    """Verify the input parameter"""
    logger = params['logger']
    args_required = ['guestname', 'snapshotname']
    for arg in args_required:
        if arg not in params:
            logger.error("Argument '%s' is required" % arg)
            return 1

    return 0

def check_domain_state(conn, guestname, logger):
    """ check if the domain exists and in shutdown state as well """
    guest_names = conn.listDefinedDomains()

    if guestname not in guest_names:
        logger.error("%s is running or does not exist" % guestname)
        return False
    else:
        return True

def revert(params):
    """ snapshot revert a snapshot for a given guest,
        this case could be with other cases togerther to
        check the functionality of snapshot
    """
    logger = params['logger']
    params_check_result = check_params(params)
    if params_check_result:
        return 1

    guestname = params['guestname']
    snapshotname = params['snapshotname']

    util = utils.Utils()
    uri = params['uri']
    conn = libvirt.open(uri)

    logger.info("the uri is %s" % uri)

    logger.info("checking if the guest is poweroff")
    if not check_domain_state(conn, guestname, logger):
        logger.error("checking failed")
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    try:
        try:
            logger.info("revert a snapshot for %s" % guestname)
            domobj = conn.lookupByName(guestname)
            snap = domobj.snapshotLookupByName(snapshotname, 0)
            domobj.revertToSnapshot(snap, 0)
            logger.info("revert snapshot succeeded")
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0

def revert_clean(params):
    """ clean testing environment """
    return 0

