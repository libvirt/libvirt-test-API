#!/usr/bin/env python
# Detach a disk from domain

import os
import re
import sys
import time

import libvirt
from libvirt import libvirtError

from src import sharedmod
from utils import utils
from utils import xml_builder

required_params = ('guestname', 'virt_type', 'imagename', 'hdmodel',)
optional_params = {}

def check_guest_status(domobj):
    """Check guest current status"""
    state = domobj.info()[0]
    if state == libvirt.VIR_DOMAIN_SHUTOFF or state == libvirt.VIR_DOMAIN_SHUTDOWN:
    # add check function
        return False
    else:
        return True

def check_detach_disk(num1, num2):
    """Check detach disk result via simple disk number
       comparison
    """
    if num2 < num1:
        return True
    else:
        return False

def detach_disk(params):
    """Detach a disk to domain from xml"""
    logger = params['logger']
    guestname = params['guestname']
    imagename = params['imagename']
    disktype = params['hdmodel']

    conn = sharedmod.libvirtobj['conn']
    domobj = conn.lookupByName(guestname)

    # Detach disk
    xmlobj = xml_builder.XmlBuilder()
    diskxml = xmlobj.build_disk(params)
    logger.debug("disk xml:\n%s" %diskxml)

    disk_num1 = utils.dev_num(guestname, "disk")
    logger.debug("original disk number: %s" %disk_num1)

    if disktype == "virtio":
        if check_guest_status(domobj):
            pass
        else:
            domobj.create()
            time.sleep(90)

    try:
        domobj.detachDevice(diskxml)
        disk_num2 = utils.dev_num(guestname, "disk")
        logger.debug("update disk number to %s" %disk_num2)
        if  check_detach_disk(disk_num1, disk_num2):
            logger.info("current disk number: %s\n" %disk_num2)
        else:
            logger.error("fail to detach a disk to guest: %s\n" %disk_num2)
            return 1
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        logger.error("detach %s disk from guest %s" % (imagename, guestname))
        return 1

    return 0
