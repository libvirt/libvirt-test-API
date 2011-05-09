#!/usr/bin/env python
""""virsh snapshot-delete" testing
   mandatory arguments: guestname snapshotname
"""

__author__ = "Guannan Ren <gren@redhat.com>"
__date__ = "Sat Feb 19, 2011"
__version__ = "0.1.0"
__credits__ = "Copyright (C) 2011 Red Hat, Inc."
__all__ = ['delete', 'check_params',
           'check_domain_state', 'delete_check']

import os
import sys
import re

def append_path(path):
    """Append root path of package"""
    if path in sys.path:
        pass
    else:
        sys.path.append(path)

pwd = os.getcwd()
result = re.search('(.*)libvirt-test-API', pwd)
append_path(result.group(0))

from lib import connectAPI
from lib import snapshotAPI
from lib import domainAPI
from utils.Python import utils
from exception import LibvirtAPI

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

def check_domain_state(domobj, guestname, logger):
    """ check if the domain exists and in shutdown state as well """
    guest_names = domobj.get_defined_list()

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
    uri = util.get_uri('127.0.0.1')
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    logger.info("the uri is %s" % uri)
    domobj = domainAPI.DomainAPI(virconn)
    snap_obj = snapshotAPI.SnapshotAPI(virconn)

    logger.info("checking if the guest is poweroff")
    if not check_domain_state(domobj, guestname, logger):
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
        logger.info("delete a snapshot for %s" % guestname)
        snap_obj.delete(guestname, snapshotname)
        if not delete_check(guestname, snapshotname, "noexist", logger):
            logger.error("after deleting, the corresponding \
                         xmlfile still exists in %s" % SNAPSHOT_DIR)
            return 1
        else:
            logger.info("delete snapshot %s succeeded" % snapshotname)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
(e.response()['message'], e.response()['code']))
        return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0
















