#!/usr/bin/evn python
"""this test case is used for testing define
   a network from xml
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Mon Feb 9, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_define_network', 'define']

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
        elif len(params[key]) == 0:
            logger.error("%s value is empty, please inputting a value" %key)
            return 1
        else:
            pass

def check_network_define(networkname, logger):
    """Check define network result, if define network is successful,
       networkname.xml will exist under /etc/libvirt/qemu/networks/
       and can use virt-xml-validate tool to check the file validity
    """
    path = "/etc/libvirt/qemu/networks/%s.xml" % networkname
    logger.debug("%s xml file path: %s" % (networkname, path))
    #valid = "virt-xml-validate %s" % path
    #stat, ret = commands.getstatusoutput(valid)
    #logger.debug("virt-xml-validate exit status: %d" % stat)
    #logger.debug("virt-xml-validate exit result: %s" % ret)
    #if os.access(path, os.R_OK) and stat == 0:
    if os.access(path, os.R_OK):
        return True
    else:
        return False

def define(params):
    """Define a network from xml"""
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

    if check_network_define(networkname, logger):
        logger.error("%s network is defined" % networkname)
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    xmlobj = xmlbuilder.XmlBuilder()
    netxml = xmlobj.build_network(params)
    logger.debug("network xml:\n%s" % netxml)

    net_num1 = netobj.get_define_number()
    logger.info("original network define number: %s" % net_num1)

    try:
        try:
            netobj.define(netxml)
            net_num2 = netobj.get_define_number()
            if check_network_define(networkname, logger) and net_num2 > net_num1:
                logger.info("current network define number: %s" % net_num2)
                logger.info("define %s network is successful" % networkname)
                test_result = True
            else:
                logger.error("%s network is undefined" % networkname)
                test_result = False
                return 1
        except LibvirtAPI, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.response()['message'], e.response()['code']))
            logger.error("define a network from xml: \n%s" % netxml)
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
