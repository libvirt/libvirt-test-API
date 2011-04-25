#!/usr/bin/env python
"""for testing the shutdown function of domain
   mandatory arguments: guestname
"""

__author__ = "Guannan Ren <gren@redhat.com>"
__date__ = "Web March 24, 2010"
__version__ = "0.1.0"
__credits__ = "Copyright (C) 2010 Red Hat, Inc."
__all__ = ['destroy', 'check_params']

import os
import sys
import re
import time

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
from lib import domainAPI
from utils.Python import utils
from exception import LibvirtAPI

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
       guestname -- same as the domain name

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

    # Connect to local hypervisor connection URI
    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    # Get running domain by name
    dom_obj = domainAPI.DomainAPI(virconn)
    dom_name_list = dom_obj.get_list()
    if guestname not in dom_name_list:
        logger.error("guest %s doesn't exist or not be running." % guestname)
        conn.close()
        logger.info("closed hypervisor connection")
        return 1
    timeout = 60
    logger.info('destroy domain')

    # Get domain ip
    mac = util.get_dom_mac_addr(guestname)
    logger.info("get ip by mac address")
    ip = util.mac_to_ip(mac, 180)
    logger.info("the ip address of guest is %s" % ip)

    # Destroy domain
    try:
        dom_obj.destroy(guestname)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
                     (e.response()['message'], e.response()['code']))
        logger.error("fail to destroy domain")
        return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    # Check domain status by ping ip
    while timeout:
        time.sleep(10)
        timeout -= 10
        logger.info(str(timeout) + "s left")

        logger.info('ping guest')

        if util.do_ping(ip, 30):
            logger.error('The guest is still active, IP: ' + str(ip))
            return 1
        else:
            logger.info("domain %s is destroied successfully" % guestname)
            break

    if timeout <= 0:
        logger.error("the domain couldn't be destroied within 60 secs.")
        return 1

    return 0

def destroy_clean(params):
    """ clean testing environment """
    pass
