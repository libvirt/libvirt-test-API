#!/usr/bin/env python

import os
import re
import sys

import libvirt
from libvirt import libvirtError

from src import sharedmod
from utils import xml_builder

required_params = ('ifacename', 'ifacetype',)
optional_params = {}

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
    global logger
    logger = params['logger']
    ifacename = params['ifacename']
    params['dhcp'] = 'yes'

    conn = sharedmod.libvirtobj['conn']

    if check_define_interface(ifacename):
        logger.error("interface %s have been defined" % ifacename)
        return 1

    xmlobj = xml_builder.XmlBuilder()
    iface_xml = xmlobj.build_host_interface(params)
    logger.debug("interface xml:\n%s" %iface_xml)

        try:
            conn.interfaceDefineXML(iface_xml, 0)
            if  check_define_interface(ifacename):
                logger.info("define a interface form xml is successful")
            else:
                logger.error("fail to check define interface")
                return 1
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            logger.error("fail to define a interface from xml")
            return 1

    return 0
