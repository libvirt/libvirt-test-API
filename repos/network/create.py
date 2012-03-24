#!/usr/bin/evn python
"""this test case is used for testing create
   a network from xml
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Wed Mar 31, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'create', 'check_network_status']

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
from utils.Python import xmlbuilder
from exception import LibvirtAPI


def usage(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    keys = ['networkname', 'bridgename', 'bridgeip', 'bridgenetmask', \
'netstart', 'netend', 'netmode']
    for key in keys:
        if key not in params:
            logger.error("%s is required" %key)
            return 1
def check_network_status(*args):
    """Check current network status, it will return True if
       current network is inactive, otherwise, return False
    """
    (networkname, netobj, logger) = args

    net_list = netobj.network_list()
    logger.debug("current active network list:")
    logger.debug(net_list)
    if networkname not in net_list:
        return True
    else:
        return False

def create(params):
    """Create a network from xml"""
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

    if not check_network_status(networkname, netobj, logger):
        logger.error("the %s network is running" % networkname)
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    xmlobj = xmlbuilder.XmlBuilder()
    netxml = xmlobj.build_network(params)
    logger.debug("%s network xml:\n%s" % (networkname, netxml))

    net_num1 = netobj.get_number()
    logger.info("original network active number: %s" % net_num1)

    try:
        try:
            netobj.create(netxml)
            net_num2 = netobj.get_number()
            if  not check_network_status(networkname, netobj, logger) and \
                    net_num2 > net_num1:
                logger.info("current network active number: %s\n" % net_num2)
                test_result = True
            else:
                logger.error("the %s network is inactive" % networkname)
                logger.error("fail to create network from :\n%s" % netxml)
                test_result = False
        except LibvirtAPI, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.response()['message'], e.response()['code']))
            logger.error("create a network from xml: \n%s" % netxml)
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
