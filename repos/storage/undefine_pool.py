#!/usr/bin/env python
"""this test case is used for testing undefine
   a specific name storage pool
"""

import os
import re
import sys

import libvirt
from libvirt import libvirtError

from utils.Python import utils

def usage(params):
    """Verify inputing parameter dictionary"""
    keys = ['poolname']
    for key in keys:
        if key not in params:
            logger.error("%s is required" %key)
            logger.info("please input the following argument:")
            logger.info(keys)
            return False
        elif len(params[key]) == 0:
            logger.error("%s value is empty, please inputting a value" %key)
            return False
        else:
            return True

def display_pool_info(conn):
    """Display current storage pool information"""
    logger.debug("current define storage pool: %s" % conn.listDefinedStoragePools())
    logger.debug("current active storage pool: %s" % conn.listStoragePools())

def check_pool_undefine(poolname):
    """Check undefine storage pool result, if undefine storage is successful,
       poolname.xml will not exist under /etc/libvirt/storage/
    """
    path = "/etc/libvirt/storage/%s.xml" % poolname
    logger.debug("%s xml file path: %s" % (poolname, path))
    if not os.access(path, os.R_OK):
        return True
    else:
        return False

def undefine_pool(params):
    """Undefine a specific name storage pool"""
    global logger
    logger = params['logger']

    if not usage(params):
        return 1

    logger = params['logger']
    poolname = params['poolname']

    util = utils.Utils()
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
        logger.error("%s is active" % poolname)
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    pool_num1 = conn.numOfDefinedStoragePools()
    logger.info("original storage pool define number: %s" % pool_num1)
    display_pool_info(conn)

    try:
        try:
            logger.info("undefine %s storage pool" % poolname)
            poolobj.undefine()
            pool_num2 = conn.numOfDefinedStoragePools()
            logger.info("current storage pool define number: %s" % pool_num2)
            display_pool_info(conn)
            if check_pool_undefine(poolname) and pool_num2 < pool_num1:
                logger.info("undefine %s storage pool is successful" % poolname)
                return 0
            else:
                logger.error("%s storage pool is undefined" % poolname)
                return 1
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")
