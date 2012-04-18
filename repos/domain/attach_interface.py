#!/usr/bin/env python
# Attach interface to domain

import os
import re
import sys

import libvirt
from libvirt import libvirtError

from src import sharedmod
from utils import utils
from utils import xmlbuilder

required_params = ('guestname', 'ifacetype', 'source',)
optional_params = ('hdmodel',)

def check_guest_status(guestname, domobj):
    """Check guest current status"""
    state = domobj.get_state(guestname)
    if state == "shutoff" or state == "shutdown":
    # add check function
        return False
    else:
        return True

def check_attach_interface(num1, num2):
    """Check attach interface result via simple interface number comparison """
    if num2 > num1:
        return True
    else:
        return False

def attach_interface(params):
    """Attach a interface to domain from xml"""
    logger = params['logger']
    guestname = params['guestname']
    conn = sharedmod.libvirtobj['conn']

    domobj = conn.lookupByName(guestname)

    # Generate interface xml
    xmlobj = xmlbuilder.XmlBuilder()
    interfacexml = xmlobj.build_interface(params)
    logger.debug("interface xml:\n%s" %interfacexml)

    iface_num1 = utils.dev_num(guestname, "interface")
    logger.debug("original interface number: %s" %iface_num1)

    # Attach interface to domain
    try:
        domobj.attachDeviceFlags(interfacexml, 0)
        iface_num2 = utils.dev_num(guestname, "interface")
        logger.debug("update interface number to %s" %iface_num2)
        if  check_attach_interface(iface_num1, iface_num2):
            logger.info("current interface number: %s" %iface_num2)
        else:
            logger.error("fail to attach a interface to guest: %s" %iface_num2)
            return 1
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        logger.error("attach a interface to guest %s" % guestname)
        return 1

    return 0
