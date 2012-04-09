#!/usr/bin/env python

import os
import sys
import re
import time
import commands

import libvirt
from libvirt import libvirtError

from utils import utils
from utils import xmlbuilder

QEMU_IMAGE_FORMAT = "qemu-img info %s |grep format |awk -F': ' '{print $2}'"

required_params = ('guestname')
optional_params = ()

def check_params(params):
    """Verify the input parameter"""
    logger = params['logger']
    args_required = ['guestname']
    for arg in args_required:
        if arg not in params:
            logger.error("Argument '%s' is required" % arg)
            return 1

    if params['guestname'] == "":
        logger.error("value of guestname is empty")
        return 1

    return 0

def check_domain_image(domobj, util, guestname, logger):
    """ensure that the state of guest is poweroff
       and its disk image is the type of qcow2
    """
    dom_xml = domobj.XMLDesc(0)
    disk_path = utils.get_disk_path(dom_xml)
    status, ret = commands.getstatusoutput(QEMU_IMAGE_FORMAT % disk_path)
    if status:
        logger.error("executing "+ "\"" + QEMU_IMAGE_FORMAT % guestname + "\"" + " failed")
        logger.error(ret)
        return False
    else:
        format = ret
        if format == "qcow2":
            return True
        else:
            logger.error("%s has a disk %s with type %s, \
                          only qcow2 supports internal snapshot" % \
                          (guestname, disk_path, format))
            return False

def internal_create(params):
    """ create an internal snapshot for a given guest,
        this case could be with other cases togerther to
        check the functionality of snapshot
    """
    logger = params['logger']
    params_check_result = check_params(params)
    if params_check_result:
        return 1
    guestname = params['guestname']

    if not params.has_key('snapshotname'):
        params['snapshotname'] = str(int(time.time()))

    uri = params['uri']
    logger.info("the uri is %s" % uri)

    conn = libvirt.open(uri)
    guest_names = conn.listDefinedDomains()
    if guestname not in guest_names:
        logger.error("%s is not poweroff or doesn't exist" % guestname)
        return 1

    domobj = conn.lookupByName(guestname)

    logger.info("checking the format of its disk")
    if not check_domain_image(domobj, util, guestname, logger):
        logger.error("checking failed")
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    xmlobj = xmlbuilder.XmlBuilder()
    snapshot_xml = xmlobj.build_domain_snapshot(params)
    logger.debug("%s snapshot xml:\n%s" % (guestname, snapshot_xml))

    try:
        try:
            logger.info("create a snapshot for %s" % guestname)
            domobj.snapshotCreateXML(snapshot_xml, 0)
            logger.info("creating snapshot succeeded")
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0

def internal_create_clean(params):
    """ clean testing environment """
    return 0
