#!/usr/bin/evn python
"""this test case is used for testing destroy network"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Tue Mar 30, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'destroy', 'check_network_status']

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

from lib.Python import connectAPI
from lib.Python import networkAPI
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

def check_network_status(*args):
    """Check current network status, it will return True if 
       current network is active, otherwise, return False
    """
    (networkname, netobj, logger) = args

    net_list = netobj.network_list()
    logger.debug("current active network list:")
    logger.debug(net_list)
    if networkname in net_list:
        return True
    else:
        return False

def destroy(params):
    """destroy network"""
    usage(params)

    logger = params['logger']
    networkname = params['networkname']
    
    test_result = False

    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')

    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    caps = conn.get_caps()
    logger.debug(caps)

    netobj = networkAPI.NetworkAPI(virconn)

    if not check_network_status(networkname, netobj, logger):
        logger.error("the %s network is inactive" % networkname)
        return 1

    net_num1 = netobj.get_number()
    logger.info("original network active number: %s" % net_num1)

    try:
        netobj.destroy(networkname)
        net_num2 = netobj.get_number()
        if not check_network_status(networkname, netobj, logger) and \
net_num1 > net_num2:
            logger.info("current network active number: %s\n" % net_num2)
            logger.info("destroy %s network successful" % networkname)
            test_result = True
        else:
            logger.error("the %s network is still running" % networkname)
            test_result = False
            return 1
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" \
% (e.response()['message'], e.response()['code']))
        logger.error("fail to destroy %s network" % networkname)
        test_result = False
        return 1
    time.sleep(3)
    if test_result:
        return 0
    else:
        return 1
