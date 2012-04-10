#!/usr/bin/env python
"""this test case is used for testing define
   a netfs type storage pool from xml
"""

import os
import re
import sys

import libvirt
from libvirt import libvirtError

from utils import utils
from utils import xmlbuilder

def usage(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']
    # targetpath is optional argument"
    keys = ['poolname', 'pooltype', 'sourcename', 'sourcepath']
    for key in keys:
        if key not in params:
            logger.error("%s is required, targetpath is optional argument" %key)
            logger.info("please input the following argument:")
            logger.info(keys)
            return False
        elif len(params[key]) == 0:
            logger.error("%s value is empty, please inputting a value" %key)
            return False
        else:
            return True

def display_pool_info(conn, logger):
    """Display current storage pool information"""
    logger.debug("current define storage pool: %s" % conn.listDefinedStoragePools())
    logger.debug("current active storage pool: %s" % conn.listStoragePools())

def check_pool_define(poolname, logger):
    """Check define storage pool result, if define storage is successful,
       poolname.xml will exist under /etc/libvirt/storage/
       and can use virt-xml-validate tool to check the file validity
    """
    path = "/etc/libvirt/storage/%s.xml" % poolname
    logger.debug("%s xml file path: %s" % (poolname, path))

    if os.access(path, os.R_OK):
        return True
    else:
        return False

def define_netfs_pool(params):
    """Define a netfs type storage pool from xml"""
    if not usage(params):
        return 1

    logger = params['logger']
    poolname = params['poolname']

    uri = params['uri']

    conn = libvirt.open(uri)

    if check_pool_define(poolname, logger):
        logger.error("%s storage pool is defined" % poolname)
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    xmlobj = xmlbuilder.XmlBuilder()
    poolxml = xmlobj.build_pool(params)
    logger.debug("storage pool xml:\n%s" % poolxml)

    pool_num1 = conn.numOfDefinedStoragePools()
    logger.info("original storage pool define number: %s" % pool_num1)
    display_pool_info(conn, logger)

    try:
        try:
            logger.info("define %s storage pool" % poolname)
            conn.storagePoolDefineXML(poolxml, 0)
            pool_num2 = conn.numOfDefinedStoragePools()
            logger.info("current storage pool define number: %s" % pool_num2)
            display_pool_info(conn, logger)
            if check_pool_define(poolname, logger) and pool_num2 > pool_num1:
                logger.info("define %s storage pool is successful" % poolname)
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

    return 0
