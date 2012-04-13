#!/usr/bin/env python
# Detach a disk from domain

import os
import re
import sys
import time

import libvirt
from libvirt import libvirtError

from utils import utils
from utils import xmlbuilder

required_params = ('guestname', 'guesttype', 'imagename', 'hdmodel',)
optional_params = ()

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
    test_result = False

    # Connect to local hypervisor connection URI
    uri = params['uri']
    conn = libvirt.open(uri)
    domobj = conn.lookupByName(guestname)

    # Detach disk
    xmlobj = xmlbuilder.XmlBuilder()
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
        try:
            domobj.detachDevice(diskxml)
            disk_num2 = utils.dev_num(guestname, "disk")
            logger.debug("update disk number to %s" %disk_num2)
            if  check_detach_disk(disk_num1, disk_num2):
                logger.info("current disk number: %s\n" %disk_num2)
                test_result = True
            else:
                logger.error("fail to detach a disk to guest: %s\n" %disk_num2)
                test_result = False
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            logger.error("detach %s disk from guest %s" % (imagename, guestname))
            test_result = False
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    if test_result:
        return 0
    else:
        return -1

def detach_disk_clean(params):
    """ clean testing environment """
    pass
