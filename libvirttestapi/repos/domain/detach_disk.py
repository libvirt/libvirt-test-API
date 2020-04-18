# Copyright (C) 2010-2012 Red Hat, Inc.
# This work is licensed under the GNU GPLv2 or later.
# Detach a disk from domain

import time
import libvirt

from libvirt import libvirtError
from libvirttestapi.utils import utils
from libvirttestapi.repos.domain.start import start

required_params = ('guestname', 'hddriver')
optional_params = {'imageformat': 'raw',
                   'volumepath': '/var/lib/libvirt/images',
                   'volume': 'attacheddisk',
                   'xml': 'xmls/disk.xml',
                   }


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
    hddriver = params['hddriver']
    xmlstr = params['xml']

    imageformat = params.get('imageformat', 'raw')
    volumepath = params.get('diskpath', '/var/lib/libvirt/images')
    volume = params.get('volume', 'attacheddisk')

    diskpath = volumepath + "/" + volume
    xmlstr = xmlstr.replace('DISKPATH', diskpath)

    if hddriver == 'virtio':
        xmlstr = xmlstr.replace('DEV', 'vdb')
    elif hddriver == 'ide':
        xmlstr = xmlstr.replace('DEV', 'hdb')
    elif hddriver == 'scsi':
        xmlstr = xmlstr.replace('DEV', 'sdb')

    logger.debug("disk xml:\n%s" % xmlstr)

    disk_num1 = utils.dev_num(guestname, "disk")
    logger.debug("original disk number: %s" % disk_num1)

    #Sleep time for windows guest
    time.sleep(15)

    try:
        conn = libvirt.open()
        domobj = conn.lookupByName(guestname)
        domobj.detachDevice(xmlstr)
        # Add sleep to wait detach disk finish
        time.sleep(15)
        disk_num2 = utils.dev_num(guestname, "disk")
        logger.debug("update disk number to %s" % disk_num2)
        if check_detach_disk(disk_num1, disk_num2):
            logger.info("current disk number: %s\n" % disk_num2)
        else:
            logger.error("fail to detach a disk to guest: %s\n" % disk_num2)
            return 1
    except libvirtError as err:
        logger.error("API error message: %s, error code is %s"
                     % (err.get_error_message(), err.get_error_code()))
        logger.error("detach %s disk from guest %s" % (xmlstr, guestname))
        return 1

    return 0


def detach_disk_clean(params):
    """
    Cleanup the test environment.
    """

    logger = params['logger']
    ret_flag = params.get("ret_flag")
    logger.info("The test return %s, try to cleanup...\n" % ret_flag)

    conn = libvirt.open()
    guestname = params['guestname']
    domobj = conn.lookupByName(guestname)

    if not domobj.isActive():
        logger.info("Start the domain")
        start(params)
    return 0
