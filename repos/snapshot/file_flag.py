#!/usr/bin/env python
""" create a flag file in the guest OS
   mandatory arguments: guestname, username, password
"""

import os
import sys
import re
import time

import libvirt
from libvirt import libvirtError

from utils import utils
from utils import check

FLAG_FILE = "snapshot_flag"
MAKE_FLAG = "rm -f /tmp/%s; touch /tmp/%s " % (FLAG_FILE, FLAG_FILE)

def return_close(conn, logger, ret):
    conn.close()
    logger.info("closed hypervisor connection")
    return ret

def check_params(params):
    """Verify the input parameter"""
    logger = params['logger']
    args_required = ['guestname', 'username', 'password']
    for arg in args_required:
        if arg not in params:
            logger.error("Argument '%s' is required" % arg)
            return 1

    return 0

def check_domain_running(conn, guestname, logger):
    """ check if the domain exists and in running state as well """
    guest_names = []
    ids = conn.listDomainsID()
    for id in ids:
        obj = conn.lookupByID(id)
        guest_names.append(obj.name())

    if guestname not in guest_names:
        logger.error("%s is not running or does not exist" % guestname)
        return False
    else:
        return True

def make_flag(chk, ipaddr, username, password, logger):
    """ enter guest OS, create a file in /tmp folder """
    ret = chk.remote_exec_pexpect(ipaddr, username, password, MAKE_FLAG)
    if ret == "TIMEOUT!!!":
        logger.error("connecting to guest OS timeout")
        return False
    elif ret != '':
        logger.error("failed to make flag in guest OS, %s" % ret)
        return False
    else:
        logger.info("flag %s is created in /tmp folder" % FLAG_FILE)
        return True

def file_flag(params):
    """ create a new file in the /tmp folder of the guest
        as a flag
    """
    logger = params['logger']
    params_check_result = check_params(params)
    if params_check_result:
        return 1

    guestname = params['guestname']
    username = params['username']
    password = params['password']

    chk = check.Check()
    uri = params['uri']
    conn = libvirt.open(uri)

    logger.info("the uri is %s" % uri)

    if not check_domain_running(conn, guestname, logger):
        logger.error("need a running guest")
        return return_close(conn, logger, 1)

    logger.info("get the mac address of vm %s" % guestname)
    mac = utils.get_dom_mac_addr(guestname)
    logger.info("the mac address of vm %s is %s" % (guestname, mac))

    timeout = 300
    while timeout:
        ipaddr = utils.mac_to_ip(mac, 180)
        if not ipaddr:
            logger.info(str(timeout) + "s left")
            time.sleep(10)
            timeout -= 10
        else:
            logger.info("the ip address of vm %s is %s" % (guestname, ipaddr))
            break

    if timeout == 0:
        logger.info("vm %s failed to get ip address" % guestname)
        return return_close(conn, logger, 1)

    if not make_flag(chk, ipaddr, username, password, logger):
        logger.error("making flag in guest %s failed" % guestname)
        return return_close(conn, logger, 1)
    else:
        logger.info("making flag in guest %s succeeded" % guestname)

    return return_close(conn, logger, 0)

def file_flag_clean(params):
    """ clean testing environment """
    return 0
