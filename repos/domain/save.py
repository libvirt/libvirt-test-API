#!/usr/bin/env python
# Save domain as a statefile

import os
import re
import sys

import libvirt
from libvirt import libvirtError

from utils import utils

required_params = ('guestname', 'filepath')
optional_params = ()

def get_guest_ipaddr(*args):
    """Get guest ip address"""
    (guestname, util, logger) = args

    mac = utils.get_dom_mac_addr(guestname)
    logger.debug("guest mac address: %s" %mac)

    ipaddr = utils.mac_to_ip(mac, 15)
    logger.debug("guest ip address: %s" %ipaddr)

    if utils.do_ping(ipaddr, 20) == 1:
        logger.info("ping current guest successfull")
        return ipaddr
    else:
        logger.error("Error: can't ping current guest")
        return None

def check_guest_status(*args):
    """Check guest current status"""
    (domobj, logger) = args

    state = domobj.info()[0]
    logger.debug("current guest status: %s" % state)

    if state == libvirt.VIR_DOMAIN_SHUTOFF or \
       state == libvirt.VIR_DOMAIN_SHUTDOWN or \
       state == libvirt.VIR_DOMAIN_BLOCKED:
        return False
    else:
        return True

def check_guest_save(*args):
    """Check save domain result, if save domain is successful,
       guestname.save will exist under /tmp directory and guest
       can't be ping and status is paused
    """
    (guestname, domobj, util, logger) = args

    if not check_guest_status(domobj, logger):
        if not get_guest_ipaddr(guestname, util, logger):
            return True
        else:
            return False
    else:
        return False

def save(params):
    """Save domain to a disk file"""
    logger = params['logger']
    guestname = params['guestname']
    filepath = params['filepath']
    test_result = False

    # Connect to local hypervisor connection URI
    uri = params['uri']
    conn = libvirt.open(uri)
    domobj = conn.lookupByName(guestname)

    # Save domain
    ipaddr = get_guest_ipaddr(guestname, util, logger)

    if not check_guest_status(domobj, logger):
        logger.error("Error: current guest status is shutoff")
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    if not ipaddr:
        logger.error("Error: can't get guest ip address")
        conn.close()
        logger.info("closed hypervisor connection")
        return 1
    try:
        try:
            domobj.save(filepath)
            if check_guest_save(guestname, domobj, util, logger):
                logger.info("save %s domain successful" %guestname)
                test_result = True
            else:
                logger.error("Error: fail to check save domain")
                test_result = False
                return 1
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            logger.error("Error: fail to save %s domain" %guestname)
            test_result = False
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    if test_result:
        return 0
    else:
        return 1

def save_clean(params):
    """ clean testing environment """
    logger = params['logger']
    filepath = params['filepath']
    if os.path.exists(filepath):
        logger.info("remove dump file from save %s" % filepath)
        os.remove(filepath)
