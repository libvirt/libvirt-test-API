#!/usr/bin/env python
"""this test case is used for testing
   define interface from xml
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Tue Apr 13, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_define_interface',
           'display_current_interface', 'define']


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
from lib import interfaceAPI
from utils.Python import utils
from utils.Python import xmlbuilder
from exception import LibvirtAPI


def usage(params):
    """Verify inputing parameter dictionary"""
#    keys = ['ifacename', 'ifacetype', 'family', 'prefix', 'address']
    keys = ['ifacename', 'ifacetype']
    logger.info("inputting argument dictionary: %s" % params)
    for key in keys:
        if key not in params:
            logger.error("%s is required" %key)
            return 1
        elif len(params[key]) == 0:
            logger.error("%s value is empty, please inputting a value" %key)
            return 1
        else:
            pass

def display_current_interface(ifaceobj):
    """Display current host interface information"""
    logger.debug("current active host interface number: %s " \
% ifaceobj.get_active_number())
    logger.debug("current active host interface list: %s " \
% ifaceobj.get_active_list())
    logger.debug("current defined host interface number: %s " \
% ifaceobj.get_defined_number())
    logger.debug("current defined host interface list: %s " \
% ifaceobj.get_defined_list())

def check_define_interface(ifacename):
    """Check defining interface result, if define interface is successful,
       ifcfg-ifacename will exist under /etc/sysconfig/network-scripts/
    """
    path = "/etc/sysconfig/network-scripts/ifcfg-%s" % ifacename
    if os.access(path, os.R_OK):
        return True
    else:
        return False


def define(params):
    """Define a specific interface from xml"""
    test_result = False
    global logger
    logger = params['logger']

    usage(params)

    ifacename = params['ifacename']
    params['dhcp'] = 'yes'

    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')

    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    caps = conn.get_caps()
    logger.debug(caps)

    if check_define_interface(ifacename):
        logger.error("interface %s have been defined" % ifacename)
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    ifaceobj = interfaceAPI.InterfaceAPI(virconn)

    xmlobj = xmlbuilder.XmlBuilder()
    iface_xml = xmlobj.build_host_interface(params)
    logger.debug("interface xml:\n%s" %iface_xml)

    try:
        try:
            ifaceobj.define(iface_xml)
            if  check_define_interface(ifacename):
                logger.info("define a interface form xml is successful")
                test_result = True
            else:
                logger.error("fail to check define interface")
                test_result = False
                return 1
        except LibvirtAPI, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.response()['message'], e.response()['code']))
            logger.error("fail to define a interface from xml")
            test_result = False
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    if test_result:
        return 0
    else:
        return 1
