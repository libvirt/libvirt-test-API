#!/usr/bin/env python
# Attach a disk device to domain

import os
import re
import sys
import time
import commands

import libvirt
from libvirt import libvirtError

from src import sharedmod
from utils import utils

required_params = ('guestname',
                   'imageformat',
                   'hddriver',)
optional_params = {'imagesize': 1,
                   'diskpath' : '/var/lib/libvirt/images/attacheddisk',
                   'xml' : 'xmls/disk.xml',
                  }

def create_image(diskpath, seeksize, imageformat, logger):
    """Create a image file"""
    disk_create = "qemu-img create -f %s %s %sG" % \
                    (imageformat, diskpath, seeksize)
    logger.debug("the command line of creating disk images is '%s'" % \
                   disk_create)

    (status, message) = commands.getstatusoutput(disk_create)
    if status != 0:
        logger.debug(message)
        return 1

    return 0

def check_attach_disk(num1, num2):
    """Check attach disk result via simple disk number comparison """
    if num2 > num1:
        return True
    else:
        return False

def attach_disk(params):
    """Attach a disk to domain from xml"""
    logger = params['logger']
    guestname = params['guestname']
    imageformat = params['imageformat']
    hddriver = params['hddriver']
    xmlstr = params['xml']

    imagesize = int(params.get('imagesize', 1))
    diskpath = params.get('diskpath', '/var/lib/libvirt/images/attacheddisk')

    conn = sharedmod.libvirtobj['conn']

    # Create image
    if create_image(diskpath, imagesize, imageformat, logger):
        logger.error("fail to create a image file")
        return 1

    domobj = conn.lookupByName(guestname)

    if hddriver == 'virtio':
        xmlstr = xmlstr.replace('DEV', 'vdb')
    elif hddriver == 'ide':
        xmlstr = xmlstr.replace('DEV', 'hdb')
    elif hddriver == 'scsi':
        xmlstr = xmlstr.replace('DEV', 'sdb')


    logger.debug("disk xml:\n%s" % xmlstr)

    disk_num1 = utils.dev_num(guestname, "disk")
    logger.debug("original disk number: %s" %disk_num1)

    # Attach disk to domain
    try:
        domobj.attachDevice(xmlstr)
        disk_num2 = utils.dev_num(guestname, "disk")
        logger.debug("update disk number to %s" %disk_num2)
        if  check_attach_disk(disk_num1, disk_num2):
            logger.info("current disk number: %s\n" %disk_num2)
        else:
            logger.error("fail to attach a disk to guest: %s\n" %disk_num2)
            return 1
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        logger.error("attach %s disk to guest %s" % (diskpath, guestname))
        return 1

    return 0
