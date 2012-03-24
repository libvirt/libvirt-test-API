#!/usr/bin/evn python
"""this test case is used for testing undefine
   the network
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Mon Feb 9, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_undefine_network', 'undefine']

import time
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
from lib import networkAPI
from utils.Python import utils
from exception import LibvirtAPI


def usage(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    keys = ['networkname']
    for key in keys:
        if key not in params:
            logger.error("%s is required" %key)
            return 1
        elif len(params[key]) == 0:
            logger.error("%s value is empty, please inputting a value" %key)
            return 1
        else:
            pass

def check_network_undefine(networkname):
    """Check undefine network result, if undefine network is successful,
       networkname.xml willn't exist under /etc/libvirt/qemu/networks/,
       if will return True, otherwise, return False
    """
    path = "/etc/libvirt/qemu/networks/%s.xml" % networkname
    if not os.access(path, os.R_OK):
        return True
    else:
        return False

def undefine(params):
    """Undefine a network"""
    usage(params)

    logger = params['logger']
    networkname = params['networkname']
    test_result = False

    util = utils.Utils()
    uri = params['uri']

    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    caps = conn.get_caps()
    logger.debug(caps)

    netobj = networkAPI.NetworkAPI(virconn)

    if check_network_undefine(networkname):
        logger.error("the network %s is undefine" % networkname)
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    net_num1 = netobj.get_define_number()
    logger.info("original network define number: %s" % net_num1)

    try:
        try:
            netobj.undefine(networkname)
            net_num2 = netobj.get_define_number()
            if  check_network_undefine(networkname) and net_num2 < net_num1:
                logger.info("current network define number: %s" % net_num2)
                logger.info("undefine %s network is successful" % networkname)
                test_result = True
            else:
                logger.error("the network %s is still define" % networkname)
                test_result = False
                return 1
        except LibvirtAPI, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.response()['message'], e.response()['code']))
            logger.error("fail to undefine a network")
            test_result = False
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    time.sleep(3)
    if test_result:
        return 0
    else:
        return 1
