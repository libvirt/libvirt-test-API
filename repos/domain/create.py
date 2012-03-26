#!/usr/bin/env python
"""this test case is used for testing
   create domain from xml
   mandatory arguments:guesttype
                       guestname
   optional arguments: uuid
                       memory
                       vcpu
                       disksize
                       imagepath
                       imagetype
                       hdmodel
                       nicmodel
                       ifacetype
                       source
                       flags
"""

__author__ = 'Guannan Ren: gren@redhat.com'
__date__ = 'Wed March 24, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2010 Red Hat, Inc.'
__all__ = ['usage', 'create']

import os
import re
import sys
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
from utils.Python import xmlbuilder
from exception import LibvirtAPI

NONE = 0
START_PAUSED = 1

def usage():
    print '''usage: mandatory arguments:guesttype
                           guestname
       optional arguments: uuid
                           memory
                           vcpu
                           disksize
                           imagepath
                           imagetype
                           hdmodel
                           nicmodel
                           ifacetype
                           source
                           flags
          '''

def return_close(conn, logger, ret):
    conn.close()
    logger.info("closed hypervisor connection")
    return ret

def check_params(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    keys = ['guestname', 'guesttype']
    for key in keys:
        if key not in params:
            logger.error("%s is required" %key)
            usage()
            return 1
    return 0


def create(params):
    """create a domain from xml"""
    # Initiate and check parameters
    params_check_result = check_params(params)
    if params_check_result:
        return 1
    logger = params['logger']
    guestname = params['guestname']
    test_result = False

    flags = None
    if params.has_key('flags'):
        flags = params['flags']
        if flags != "none" and flags != "start_paused":
            logger.error("flags value either \"none\" or \"start_paused\"");
            return 1

    # Connect to local hypervisor connection URI
    util = utils.Utils()
    uri = params['uri']
    conn = connectAPI.ConnectAPI(uri)
    conn.open()

    caps = conn.get_caps()
    logger.debug(caps)

    # Generate domain xml
    domobj = domainAPI.DomainAPI(conn)
    xmlobj = xmlbuilder.XmlBuilder()
    domain = xmlobj.add_domain(params)
    xmlobj.add_disk(params, domain)
    xmlobj.add_interface(params, domain)
    domxml = xmlobj.build_domain(domain)
    logger.debug("domain xml:\n%s" %domxml)

    # Create domain from xml
    try:
        if not flags or flags == "none":
            domobj.create(domxml, NONE)
        elif flags == "start_paused":
            domobj.create(domxml, START_PAUSED)
        else:
            logger.error("flags error")
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" %
                      (e.response()['message'], e.response()['code']))
        logger.error("fail to create domain %s" % guestname)
        return return_close(conn, logger, 1)

    if flags == "start_paused":
        state = domobj.get_state(guestname)
        if state == "paused":
            logger.info("guest start with state paused successfully")
            return return_close(conn, logger, 0)
        else:
            logger.error("guest state error")
            return return_close(conn, logger, 1)

    logger.info("get the mac address of vm %s" % guestname)
    mac = util.get_dom_mac_addr(guestname)
    logger.info("the mac address of vm %s is %s" % (guestname, mac))

    timeout = 600

    while timeout:
        time.sleep(10)
        timeout -= 10

        ip = util.mac_to_ip(mac, 180)

        if not ip:
            logger.info(str(timeout) + "s left")
        else:
            logger.info("vm %s power on successfully" % guestname)
            logger.info("the ip address of vm %s is %s" % (guestname, ip))
            test_result = True
            break

        if timeout == 0:
            logger.info("fail to power on vm %s" % guestname)
            test_result = False
            return return_close(conn, logger, 1)

    if test_result:
        return return_close(conn, logger, 0)
    else:
        return return_close(conn, logger, 1)
