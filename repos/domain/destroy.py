#!/usr/bin/env python
"""for testing the shutdown function of domain
   mandatory arguments: guestname
"""

import os
import sys
import re
import time

import libvirt
from libvirt import libvirtError

from utils import utils

def check_params(params):
    """Verify the input parameter"""
    args_required = ['guestname']
    for arg in args_required:
        if arg not in params:
            logger.error("Argument '%s' is required" % arg)
            return 1

    if params['guestname'] == "":
        logger.error("value of guestname is empty")
        return 1

    return 0

def destroy(params):
    """destroy domain
       Argument is a dictionary with two keys:
       {'guestname': guestname}

       logger -- an object of utils/Python/log.py
       guestname -- the domain name
       flags -- optional arguments:
                  noping: Don't do the ping test


       Return 0 on SUCCESS or 1 on FAILURE
    """
    # Initiate and check parameters
    global logger
    logger = params['logger']
    params.pop('logger')
    params_check_result = check_params(params)
    if params_check_result:
        return 1
    guestname = params['guestname']
    flags = ""
    if params.has_key('flags'):
        flags = params['flags']

    # Connect to local hypervisor connection URI
    util = utils.Utils()
    uri = params['uri']
    conn = libvirt.open(uri)

    # Get running domain by name
    guest_names = []
    ids = conn.listDomainsID()
    for id in ids:
        obj = conn.lookupByID(id)
        guest_names.append(obj.name())

    if guestname not in guest_names:
        logger.error("guest %s doesn't exist or isn't running." % guestname)
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    domobj = conn.lookupByName(guestname)

    timeout = 60
    logger.info('destroy domain')

    if not "noping" in flags:
        # Get domain ip
        mac = util.get_dom_mac_addr(guestname)
        logger.info("get ip by mac address")
        ip = util.mac_to_ip(mac, 180)
        logger.info("the ip address of guest is %s" % ip)

    # Destroy domain
    try:
        try:
            domobj.destroy()
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            logger.error("failed to destroy domain")
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    # Check domain status by ping ip
    if not "noping" in flags:
        while timeout:
            time.sleep(10)
            timeout -= 10
            logger.info(str(timeout) + "s left")

            logger.info('ping guest')

            if util.do_ping(ip, 30):
                logger.error('The guest is still active, IP: ' + str(ip))
                return 1
            else:
                logger.info("domain %s was destroyed successfully" % guestname)
                break

        if timeout <= 0:
            logger.error("the domain couldn't be destroyed within 60 seconds.")
            return 1

    return 0

def destroy_clean(params):
    """ clean testing environment """
    pass
