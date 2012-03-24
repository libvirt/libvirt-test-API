#!/usr/bin/env python
"""this test case is used for testing
   activating specific host interface
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Thu Apr 15, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_create_interface',
           'display_current_interface', 'create']


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
from lib import interfaceAPI
from utils.Python import utils
from utils.Python import xmlbuilder
from exception import LibvirtAPI


def usage(params):
    """Verify inputing parameter dictionary"""
    keys = ['ifacename']
    logger.debug("inputting argument dictionary: %s" % params)
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

def check_create_interface(ifacename, util):
    """Check creating interface result, it will can ping itself
       if create interface is successful.
    """
    hostip = util.get_ip_address(ifacename)
    logger.debug("interface %s ip address: %s" % (ifacename, hostip))
    ping_cmd = "ping -c 4 -q %s" % hostip
    stat, ret = commands.getstatusoutput(ping_cmd)
    logger.debug("ping cmds exit status: %d" % stat)
    logger.debug("ping cmds exit result: %s" % ret)
    if stat == 0:
        logger.debug("can ping itself")
        return True
    else:
        logger.error("can't ping itself")
        return False


def create(params):
    """Activate specific interface, argument params is dictionary type, and
       includes 'ifacename' key, which is a host interface name, e.g 'eth0'
    """
    test_result = False
    global logger
    logger = params['logger']

    usage(params)

    ifacename = params['ifacename']

    util = utils.Utils()
    uri = params['uri']
    try:
        hostip = util.get_ip_address(ifacename)
        logger.error("interface %s is running" % ifacename)
        logger.debug("interface %s ip address: %s" % (ifacename, hostip))
        return 1
    except:
        logger.info("interface %s is deactive" % ifacename)

    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    caps = conn.get_caps()
    logger.debug(caps)

    ifaceobj = interfaceAPI.InterfaceAPI(virconn)
    display_current_interface(ifaceobj)


    try:
        try:
            ifaceobj.create(ifacename)
            logger.info("create host interface %s" % ifacename)
            display_current_interface(ifaceobj)
            if  check_create_interface(ifacename, util):
                logger.info("create host interface %s is successful" % ifacename)
                test_result = True
            else:
                logger.error("fail to check create interface")
                test_result = False
                return 1
        except LibvirtAPI, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.response()['message'], e.response()['code']))
            logger.error("fail to create interface %s" %ifacename)
            test_result = False
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    if test_result:
        return 0
    else:
        return 1
