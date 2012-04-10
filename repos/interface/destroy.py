#!/usr/bin/env python
"""this test case is used for testing
   destroy specific host interface
"""

import os
import re
import sys
import commands

import libvirt
from libvirt import libvirtError

from utils import utils
from utils import xmlbuilder

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

def display_current_interface(conn):
    """Display current host interface information"""
    logger.debug("current active host interface number: %s " \
% conn.numOfInterfaces)
    logger.debug("current active host interface list: %s " \
% conn.listInterfaces())
    logger.debug("current defined host interface number: %s " \
% conn.numOfDefinedInterfaces())
    logger.debug("current defined host interface list: %s " \
% conn.listDefinedInterfaces())

def check_destroy_interface(hostip):
    """Check destroying interface result, it will can't ping itself
       if destroy interface is successful.
    """
    ping_cmd = "ping -c 4 -q %s" % hostip
    stat, ret = commands.getstatusoutput(ping_cmd)
    logger.debug("ping cmds exit status: %d" % stat)
    logger.debug("ping cmds exit result: %s" % ret)
    if stat != 0:
        logger.debug("can't ping itself")
        return True
    else:
        logger.error("can ping itself")
        return False


def destroy(params):
    """Deactive specific interface, argument params is dictionary type, and
       includes 'ifacename' key, which is a host interface name, e.g 'eth0'
    """
    test_result = False
    global logger
    logger = params['logger']

    usage(params)

    ifacename = params['ifacename']

    uri = params['uri']
    try:
        hostip = utils.get_ip_address(ifacename)
        logger.info("interface %s is active" % ifacename)
        logger.debug("interface %s ip address: %s" % (ifacename, hostip))
    except:
        logger.error("interface %s is deactive" % ifacename)
        return 1

    conn = libvirt.open(uri)
    ifaceobj = conn.interfaceLookupByName(ifacename)
    display_current_interface(conn)

    try:
        try:
            ifaceobj.destroy(0)
            logger.info("destroy host interface %s" % ifacename)
            display_current_interface(conn)
            if  check_destroy_interface(hostip):
                logger.info("destroy host interface %s is successful" % ifacename)
                test_result = True
            else:
                logger.error("fail to check destroy interface")
                test_result = False
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            logger.error("fail to destroy interface %s" %ifacename)
            test_result = False
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    if test_result:
        return 0
    else:
        return 1
