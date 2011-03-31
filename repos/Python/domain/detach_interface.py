#!/usr/bin/env python
"""this test case is used for testing detach
   the interface to domain from xml
   mandatory arguments: guestname
                        ifacetype
                        source
                        nicmodel
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Mon Jan 28, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_guest_status', 'check_detach_interface',
           'detach_interface']

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

from lib.Python import connectAPI
from lib.Python import domainAPI
from utils.Python import utils
from utils.Python import xmlbuilder
from exception import LibvirtAPI

def usage(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    keys = ['guestname', 'ifacetype', 'source', 'nicmodel']
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

def check_detach_interface(num1, num2):
    """Check detach interface result via simple interface number
       comparison
    """
    if num2 < num1:
        return True
    else:
        return False

def detach_interface(params):
    """Detach a interface to domain from xml"""
    # Initiate and check parameters
    usage(params)
    logger = params['logger']
    guestname = params['guestname']
    test_result = False

    # Connect to local hypervisor connection URI
    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')
    macs = util.get_dom_mac_addr(guestname)
    mac_list = macs.split("\n")
    logger.debug("mac address: \n%s" % macs)
    params['macaddr'] = mac_list[-1]

    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    caps = conn.get_caps()
    logger.debug(caps)

    # Detach disk
    domobj = domainAPI.DomainAPI(virconn)
    xmlobj = xmlbuilder.XmlBuilder()
    ifacexml = xmlobj.build_interface(params)
    logger.debug("interface xml:\n%s" % ifacexml)

    iface_num1 = util.dev_num(guestname, "interface")
    logger.debug("original interface number: %s" % iface_num1)

    if check_guest_status(guestname, domobj):
        pass
    else:
        domobj.start(guestname)
        time.sleep(90)

    try:
        domobj.detach_device(guestname, ifacexml)
        iface_num2 = util.dev_num(guestname, "interface")
        logger.debug("update interface number to %s" % iface_num2)
        if  check_detach_interface(iface_num1, iface_num2):
            logger.info("current interface number: %s" % iface_num2)
            test_result = True
        else:
            logger.error("fail to detach a interface to guest: %s" %
                          iface_num2)
            test_result = False
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
                     (e.response()['message'], e.response()['code']))
        logger.error("detach the interface from guest %s" % guestname)
        test_result = False
        return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    if test_result:
        return 0
    else:
        return -1
