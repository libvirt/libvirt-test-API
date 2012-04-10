#!/usr/bin/env python
"""Test to activate an inactivate storage pool in libvirtd """

import os
import re
import sys
import time

import libvirt
from libvirt import libvirtError

from utils import xmlbuilder

def usage(params):
    """Verify inputing parameter dictionary"""
    logger = params['logger']

    if 'poolname' not in params:
        logger.error("poolname parameter is required")
        logger.info("Please provide poolname parameter")
        return False
    elif len(params['poolname']) == 0:
        logger.error("poolname parameter is empty.")
        logger.error("Please set poolname parameter to a value.")
        return False
    else:
        return True

def display_pool_info(stg, logger):
    """Display current storage pool information"""
    logger.debug("current defined storage pool: %s" % \
                  stg.defstorage_pool_list())
    logger.debug("current active storage pool: %s" % stg.storage_pool_list())

def activate_pool(params):
    """Undefine a storage pool that's been defined and inactive"""
    logger = params['logger']
    if usage(params):
        logger.info("Params are right")
    else:
        logger.info("Params are wrong")
        return 1

    poolname = params['poolname']

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
    try:
        try:
            poolobj.create(0)
            time.sleep(5)
            if  poolobj.isActive():
                logger.info("activating %s storage pool is SUCCESSFUL!!!" % poolname)
                return 0
            else:
                logger.info("activating %s storage pool is UNSUCCESSFUL!!!" % poolname)
                return 1
        except libvirtError, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.message, e.get_error_code()))
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0
