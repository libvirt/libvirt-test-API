#!/usr/bin/env python
"""this test case is used for testing attach
   the interface to domain from xml
   mandatory arguments:guestname
                       ifacetype
                       source
   optional arguments: hdmodel
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Mon Jan 28, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_guest_status', 'check_attach_interface',
           'attach_interface']

import os
import re
import sys

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

def usage(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    keys = ['guestname', 'ifacetype', 'source']
    optional_keys = ['hdmodel']
    for key in keys:
        if key not in params:
            logger.error("%s is required" %key)
            return 1

def check_guest_status(guestname, domobj):
    """Check guest current status"""
    state = domobj.get_state(guestname)
    if state == "shutoff" or state == "shutdown":
    # add check function
        return False
    else:
        return True

def check_attach_interface(num1, num2):
    """Check attach interface result via simple interface number comparison """
    if num2 > num1:
        return True
    else:
        return False

def attach_interface(params):
    """Attach a interface to domain from xml"""
    # Initiate and check parameters
    usage(params)
    logger = params['logger']
    guestname = params['guestname']
    test_result = False

    # Connect to local hypervisor connection URI
    util = utils.Utils()
    uri = params['uri']
    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    caps = conn.get_caps()
    logger.debug(caps)

    # Generate interface xml
    domobj = domainAPI.DomainAPI(virconn)
    xmlobj = xmlbuilder.XmlBuilder()
    interfacexml = xmlobj.build_interface(params)
    logger.debug("interface xml:\n%s" %interfacexml)

    iface_num1 = util.dev_num(guestname, "interface")
    logger.debug("original interface number: %s" %iface_num1)

    # Attach interface to domain
    try:
        try:
            domobj.attach_device(guestname, interfacexml)
            iface_num2 = util.dev_num(guestname, "interface")
            logger.debug("update interface number to %s" %iface_num2)
            if  check_attach_interface(iface_num1, iface_num2):
                logger.info("current interface number: %s" %iface_num2)
                test_result = True
            else:
                logger.error("fail to attach a interface to guest: %s" %iface_num2)
                test_result = False
        except LibvirtAPI, e:
            logger.error("API error message: %s, error code is %s"  %
                         (e.response()['message'], e.response()['code']))
            logger.error("attach a interface to guest %s" % guestname)
            test_result = False
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    if test_result:
        return 0
    else:
        return -1
