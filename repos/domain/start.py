#!/usr/bin/env python

import os
import sys
import re
import time

import libvirt
from libvirt import libvirtError

from utils import utils

required_params = ('guestname')
optional_params = ()

NONE = 0
START_PAUSED = 1

def return_close(conn, logger, ret):
    conn.close()
    logger.info("closed hypervisor connection")
    return ret

def start(params):
    """Start domain

        Argument is a dictionary with two keys:
        {'logger': logger, 'guestname': guestname}

        logger -- an object of utils/log.py
        mandatory arguments : guestname -- same as the domain name
        optional arguments : flags -- domain create flags <none|start_paused|noping>

        Return 0 on SUCCESS or 1 on FAILURE
    """
    is_fail = True
    domname = params['guestname']
    logger = params['logger']
    flags = params.get('flags', '')

    if "none" in flags and "start_paused" in flags:
        logger.error("Flags error: Can't specify none and start_paused simultaneously")
        return return_close(conn, logger, 1)

    # Connect to local hypervisor connection URI
    uri = params['uri']
    conn = libvirt.open(uri)
    domobj = conn.lookupByName(domname)

    timeout = 600
    logger.info('start domain')

    try:
        if "none" in flags:
            domobj.createWithFlags(NONE)
        elif "start_paused" in flags:
            domobj.createWithFlags(START_PAUSED)
        else:
            # this covers flags = None as well as flags = 'noping'
            domobj.create()
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        logger.error("start failed")
        return return_close(conn, logger, 1)

    if "start_paused" in flags:
        state = domobj.info()[0]
        if state == libvirt.VIR_DOMAIN_PAUSED:
            logger.info("guest start with state paused successfully")
            return return_close(conn, logger, 0)
        else:
            logger.error("guest state error")
            return return_close(conn, logger, 1)

    while timeout:
        state = domobj.info()[0]
        expect_states = [libvirt.VIR_DOMAIN_RUNNING, libvirt.VIR_DOMAIN_NOSTATE, libvirt.VIR_DOMAIN_BLOCKED]

        if state in expect_states:
            break

        time.sleep(10)
        timeout -= 10
        logger.info(str(timeout) + "s left")

    if timeout <= 0:
        logger.error('The domain state is not as expected, state: ' + state)
        return return_close(conn, logger, 1)

    logger.info("Guest started")

    # Get domain ip and ping ip to check domain's status
    if not "noping" in flags:
        mac = utils.get_dom_mac_addr(domname)
        logger.info("get ip by mac address")
        ip = utils.mac_to_ip(mac, 180)

        logger.info('ping guest')
        if not utils.do_ping(ip, 300):
            logger.error('Failed on ping guest, IP: ' + str(ip))
            return return_close(conn, logger, 1)

    logger.info("PASS")
    return return_close(conn, logger, 0)

def start_clean(params):
    """ clean testing environment """
    pass
