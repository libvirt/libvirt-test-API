#!/usr/bin/evn python
"""this test case is used for testing to activate
   a virtual network
"""

__author__ = 'Guannan Ren: gren@redhat.com'
__date__ = 'Tue Mar 30, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2010 Red Hat, Inc.'
__all__ = ['usage', 'check_activated_network', 'start']

import time
import os
import re
import sys
import commands

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

def return_close(conn, logger, ret):
    conn.close()
    logger.info("closed hypervisor connection")
    return ret

def check_params(params):
    """Verify inputing parameter dictionary"""

    keys = ['networkname']
    for key in keys:
        if key not in params:
            logger.error("Argument %s is required" %key)
            return 1

def start(params):
    """activate a defined network"""

    global logger
    logger = params['logger']

    params.pop('logger')

    params_check_result = check_params(params)

    if params_check_result:
        return 1

    networkname = params['networkname']
    logger.info("the name of virtual network to be activated is %s" % \
                 networkname)

    util = utils.Utils()
    uri = params['uri']

    logger.info("uri address is %s" % uri)

    conn = connectAPI.ConnectAPI(uri)
    conn.open()

    caps = conn.get_caps()
    logger.debug(caps)

    netobj = networkAPI.NetworkAPI(conn)

    net_defined_list = netobj.defined_list()

    if networkname not in net_defined_list:
        logger.error("virtual network %s doesn't exist \
                      or is active already." % networkname)
        return return_close(conn, logger, 1)
    else:
        netxmldesc = netobj.netxml_dump(networkname)
        logger.debug("the xml description of the virtual network is %s" % \
                      netxmldesc)

    try:
        logger.info("begin to activate virtual network %s" % networkname)
        netobj.start(networkname)
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" % \
                      (e.response()['message'], e.response()['code']))
        logger.error("fail to destroy domain")
        return return_close(conn, logger, 1)

    net_activated_list = netobj.network_list()

    if networkname not in net_activated_list:
        logger.error("virtual network %s failed to be activated." % networkname)
        return return_close(conn, logger, 1)
    else:
        shell_cmd = "virsh net-list --all"
        (status, text) = commands.getstatusoutput(shell_cmd)
        logger.debug("the output of 'virsh net-list --all' is %s" % text)

    logger.info("activate the virtual network successfully.")
    time.sleep(3)

    return return_close(conn, logger, 0)
