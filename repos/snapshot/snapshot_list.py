#!/usr/bin/env python

import os
import sys
import re
import commands

SNAPSHOT_DIR = "/var/lib/libvirt/qemu/snapshot"
SNAPSHOT_LIST = "virsh snapshot-list %s |sed -n '3,$'p|awk '{print $1}'"

required_params = ('guestname')
optional_params = ()

def check_params(params):
    """Verify the input parameter"""
    logger = params['logger']
    args_required = ['guestname']
    for arg in args_required:
        if arg not in params:
            logger.error("Argument '%s' is required" % arg)
            return 1

    return 0

def snapshot_list(params):
    """check the output of snapshot_list through examining
       the files under /var/lib/libvirt/qemu/snapshot folder
    """
    logger = params['logger']
    params_check_result = check_params(params)
    if params_check_result:
        return 1

    guestname = params['guestname']

    snapshot_list = []
    status, ret = commands.getstatusoutput(SNAPSHOT_LIST % guestname)
    if status:
        logger.error("executing "+ "\"" +  VIRSH_QUIET_LIST % " " + "\"" + " failed")
        logger.error(ret)
        return 1
    else:
        snapshot_list = ret.split('\n')
        logger.info("snapshot list is %s" % snapshot_list)

    guest_snapshot_dir = os.path.join(SNAPSHOT_DIR, guestname)
    if (not os.path.isdir(guest_snapshot_dir) or not os.listdir(guest_snapshot_dir)) \
        and snapshot_list == ['']:
        logger.info("guest %s has no snapshot records" % guestname)
        return 0
    elif (not os.path.isdir(guest_snapshot_dir) or not os.listdir(guest_snapshot_dir)) \
        and snapshot_list != ['']:
        logger.error("snapshot_list output contains snapshot names: %s" % snapshot_list)
        logger.error("but the folder %s doesn't exist or is empty" % SNAPSHOT_DIR)
        return 1
    elif os.listdir(guest_snapshot_dir) and snapshot_list == ['']:
        logger.error("snapshot_list output contains no records")
        logger.error("but the folder contains snapshot xml files: %s" % \
                      os.listdir(guest_snapshot_dir))
        return 1

    logger.info("the path of snapshot for guest %s is %s" % \
                  (guestname, guest_snapshot_dir))

    snapshot_entries = os.listdir(guest_snapshot_dir)
    logger.info("%s in %s" % (snapshot_entries, guest_snapshot_dir))

    for entry in snapshot_entries:
        if not entry.endswith('.xml'):
            continue
        else:
            snapshot_name = entry[:-4]
            if snapshot_name not in snapshot_list:
                logger.error("snapshot %s is not in the output of \
                              virsh snapshot_list" % snapshot_name)
                return 1
    return 0

def snapshot_list_clean(params):
    """ clean testing environment """
    return 0

