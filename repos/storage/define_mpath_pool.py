#!/usr/bin/env python

import os
import re
import sys

import libvirt
from libvirt import libvirtError

from utils import xmlbuilder

def check_params(params):
    """Verify inputing parameter dictionary"""
    #targetpath and sourceformat are optional arguments
    #the default targetpath is /dev
    #the sourceformat is 'dos'
    mandatory_params = ['poolname', 'pooltype']
    optional_params = ['targetpath']

    for param in mandatory_params:
        if param not in params:
            logger.error("%s is required" % param)
            usage()
            return 1
        elif len(params[param]) == 0:
            logger.error("%s value is empty, please inputting a value" % param)
            return 1
        else:
            pass

def display_pool_info(conn):
    """Display current storage pool information"""
    logger.debug("current define storage pool: %s" % \
                  conn.listDefinedStoragePools())
    logger.debug("current active storage pool: %s" % conn.listStoragePools())

def check_pool_define(poolname):
    """This function will check if the storage pool with
       the given poolname existed already.It first checks
       if the storagepool xml file exists in /etc/libvirt/storage
       directory
    """
    path = "/etc/libvirt/storage/%s.xml" % poolname
    logger.debug("%s xml file path: %s" % (poolname, path))

    if os.access(path, os.R_OK):
        return True
    else:
        return False

def define_mpath_pool(params):
    """Define a mpath type storage pool from xml"""

    global logger
    logger = params['logger']

    params.pop('logger')

    params_check_result = check_params(params)

    if params_check_result:
        return 1

    poolname = params['poolname']
    pooltype = params['pooltype']

    logger.info("the poolname is %s, pooltype is %s" % (poolname, pooltype))

    uri = params['uri']

    conn = libvirt.open(uri)

    if check_pool_define(poolname):
        logger.error("%s storage pool is defined" % poolname)
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    xmlobj = xmlbuilder.XmlBuilder()
    poolxml = xmlobj.build_pool(params)
    logger.debug("storage pool xml:\n%s" % poolxml)

    pool_num1 = conn.numOfDefinedStoragePools()
    logger.info("original storage pool define number: %s" % pool_num1)
    display_pool_info(conn)

    try:
        try:
            logger.info("define %s storage pool" % poolname)
            conn.storagePoolDefineXML(poolxml, 0)
            pool_num2 = conn.numOfDefinedStoragePools()
            logger.info("current storage pool define number: %s" % pool_num2)
            display_pool_info(conn)
            if check_pool_define(poolname) and pool_num2 > pool_num1:
                logger.info("It is successful to define %s storage pool" % poolname)
                return 0
            else:
                logger.error("%s storage pool was not defined successfully" % \
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
