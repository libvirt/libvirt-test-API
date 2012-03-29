#!/usr/bin/evn python
""" Restart libvirtd testing. A running guest is required in this test.
    During libvirtd restart, the guest remains running and not affected
    by libvirtd restart.
    libvirtd:restart
        guestname
            #GUESTNAME#
"""

__author__ = 'Wayne Sun: gsun@redhat.com'
__date__ = 'Thu Aug 4, 2011'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2011 Red Hat, Inc.'
__all__ = ['restart']

import os
import re
import sys

from lib import connectAPI
from lib import domainAPI
from utils.Python import utils

VIRSH_LIST = "virsh list --all"
RESTART_CMD = "service libvirtd restart"

def check_params(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    keys = ['guestname']
    for key in keys:
        if key not in params:
            logger.error("%s is required" %key)
            return 1
    return 0

def check_domain_running(domobj, guestname, logger):
    """ check if the domain exists, may or may not be active """
    guest_names = domobj.get_list()

    if guestname not in guest_names:
        logger.error("%s doesn't exist or not running" % guestname)
        return 1
    else:
        return 0

def libvirtd_check(util, logger):
    """check libvirtd status
    """
    cmd = "service libvirtd status"
    ret, out = util.exec_cmd(cmd, shell=True)
    if ret != 0:
        logger.error("failed to get libvirtd status")
        return 1
    else:
        logger.info(out[0])

    logger.info(VIRSH_LIST)
    ret, out = util.exec_cmd(VIRSH_LIST, shell=True)
    if ret != 0:
        logger.error("failed to get virsh list result")
        return 1
    else:
        for i in range(len(out)):
            logger.info(out[i])

    return 0

def get_domain_pid(util, logger, guestname):
    """get the pid of running domain"""
    logger.info("get the pid of running domain %s"  % guestname)
    get_pid_cmd = "cat /var/run/libvirt/qemu/%s.pid" % guestname
    ret, pid = util.exec_cmd(get_pid_cmd, shell=True)
    if ret:
        logger.error("fail to get the pid of runnings domain %s" % \
                     guestname)
        return 1, ""
    else:
        logger.info("the pid of domain %s is %s" % \
                    (guestname, pid[0]))
        return 0, pid[0]

def restart(params):
    """restart libvirtd test"""
    # Initiate and check parameters
    params_check_result = check_params(params)
    if params_check_result:
        return 1

    logger = params['logger']
    guestname = params['guestname']
    util = utils.Utils()
    uri = params['uri']

    conn = connectAPI.ConnectAPI(uri)
    conn.open()
    domobj = domainAPI.DomainAPI(conn)

    logger.info("check the domain state")
    ret = check_domain_running(domobj, guestname, logger)
    if ret:
        return 1

    conn.close()

    logger.info("check the libvirtd status:")
    ret = libvirtd_check(util, logger)
    if ret:
        return 1

    # Get domain ip
    logger.info("get the mac address of domain %s" % guestname)
    mac = util.get_dom_mac_addr(guestname)
    logger.info("the mac address of domain %s is %s" % (guestname, mac))
    logger.info("get ip by mac address")
    ip = util.mac_to_ip(mac, 180)
    logger.info("the ip address of domain %s is %s" % (guestname, ip))


    logger.info("ping to domain %s" % guestname)
    if util.do_ping(ip, 0):
        logger.info("Success ping domain %s" % guestname)
    else:
        logger.error("fail to ping domain %s" % guestname)
        return 1

    ret, pid_before = get_domain_pid(util, logger, guestname)
    if ret:
        return 1

    logger.info("restart libvirtd service:")
    ret, out = util.exec_cmd(RESTART_CMD, shell=True)
    if ret != 0:
        logger.error("failed to restart libvirtd")
        for i in range(len(out)):
            logger.error(out[i])
        return 1
    else:
        for i in range(len(out)):
            logger.info(out[i])

    logger.info("recheck libvirtd status:")
    ret = libvirtd_check(util, logger)
    if ret:
        return 1

    logger.info("ping to domain %s again" % guestname)
    if util.do_ping(ip, 0):
        logger.info("Success ping domain %s" % guestname)
    else:
        logger.error("fail to ping domain %s" % guestname)
        return 1

    ret, pid_after = get_domain_pid(util, logger, guestname)
    if ret:
        return 1

    if pid_before != pid_after:
        logger.error("%s pid changed during libvirtd restart" % \
                     guestname)
        return 1
    else:
        logger.info("domain pid not change, %s keeps running during \
                     libvirtd restart" % guestname)

    return 0

def restart_clean(params):
    """ clean testing environment """
    pass

