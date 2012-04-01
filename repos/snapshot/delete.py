#!/usr/bin/env python
""""virsh snapshot-delete" testing
   mandatory arguments: guestname snapshotname
"""

import os
import sys
import re

import libvirt
from libvirt import libvirtError

from utils.Python import utils

SNAPSHOT_DIR = "/var/lib/libvirt/qemu/snapshot"

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

def delete_check(guestname, snapshotname, expected_flag, logger):
    """ after deleting, check if appropriate xml file exists or not"""
    guest_snapshot_dir = os.path.join(SNAPSHOT_DIR, guestname)
    snapshot_entries = os.listdir(guest_snapshot_dir)
    if snapshotname + ".xml" in snapshot_entries and expected_flag == "exist":
        return True
    elif snapshotname + ".xml" in snapshot_entries and expected_flag == "noexist":
        return False
    elif snapshotname + ".xml" not in snapshot_entries and expected_flag == "exist":
        return False
    elif snapshotname + ".xml" not in snapshot_entries and expected_flag == "noexist":
        return True


def delete(params):
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

    if not delete_check(guestname, snapshotname, "exist", logger):
        logger.error("no snapshot %s exists" % snapshotname)
        logger.debug("not corresponding xml file in %s" % SNAPSHOT_DIR)
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    try:
        try:
            logger.info("delete a snapshot for %s" % guestname)
            domobj = conn.lookupByName(guestname)
            snapobj = domobj.snapshotLookupByName(snapshotname, 0)
            snapobj.delete(0)
            if not delete_check(guestname, snapshotname, "noexist", logger):
                logger.error("after deleting, the corresponding \
                             xmlfile still exists in %s" % SNAPSHOT_DIR)
                return 1
            else:
                logger.info("delete snapshot %s succeeded" % snapshotname)
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0

def delete_clean(params):
    """ clean testing environment """
    return 0
