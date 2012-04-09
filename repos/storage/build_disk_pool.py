#!/usr/bin/env python

import os
import re
import sys
import time
import commands
from xml.dom import minidom

import libvirt
from libvirt import libvirtError


required_params = ('poolname')
optional_params = ()

def check_params(params):
    """Verify inputing parameter dictionary"""
    options = ['poolname']

    for option in options:
        if option not in params:
            logger.error("%s is required" % option)
            usage()
            return 1
        elif len(params[option]) == 0:
            logger.error("%s value is empty, please inputting a value" % option)
            return 1
        else:
            return 0

def get_pool_devicename_type(poolobj):
    """ get device name and partition table of the pool
        from its xml description """
    poolxml = poolobj.XMLDesc(0)

    logger.debug("the xml description of pool is %s" % poolxml)

    doc = minidom.parseString(poolxml)
    device_element = doc.getElementsByTagName('device')[0]
    source_device = device_element.attributes['path'].value

    format_element = doc.getElementsByTagName('format')[0]
    device_type = format_element.attributes['type'].value

    return source_device, device_type

def check_pool_built(source_device, device_type):
    """using parted command tool to check the validation of final result"""

    cmd = "parted -s %s print" % source_device
    ret, output = commands.getstatusoutput(cmd)
    partition_info = output.split("\n")[3]

    logger.debug("the partition information is %s" % partition_info)
    partition_table = partition_info.split(": ")[1]

    if device_type in partition_table:
        return 0
    else:
        return 1

def build_disk_pool(params):
    """ build a defined and inactive pool"""

    global logger
    logger = params['logger']

    params_check_result = check_params(params)

    if params_check_result:
        logger.error("parameters sanity check failed")
        return 1
    else:
        logger.info("parameters sanity check succeeded")

    poolname = params['poolname']
    logger.info("the poolname is %s" % (poolname))

    uri = params['uri']

    conn = libvirt.open(uri)
    pool_names = conn.listDefinedStoragePools()
    pool_names += conn.listStoragePools()

    if poolname in pool_names:
        poolobj = conn.storagePoolLookupByName(poolname)
    else:
        logger.error("%s not found\n" % poolname);
        conn.close()
        return 1

    if poolobj.isActive():
        logger.error("%s is active already" % poolname)
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    source_device, device_type = get_pool_devicename_type(poolobj)
    logger.info("the source device of the pool is %s, \
                 the partition table type is %s" % \
                 (source_device, device_type))

    try:
        try:
            logger.info("begin to build the storage pool")
            poolobj.build(0)
            time.sleep(5)
            if not check_pool_built(source_device, device_type):
                logger.info("building %s storage pool is SUCCESSFUL!!!" % poolname)
                return 0
            else:
                logger.info("building %s storage pool is UNSUCCESSFUL!!!" % \
                             poolname)
                return 1
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0
