#!/usr/bin/env python

import os
import re
import sys
import time

import libvirt
from libvirt import libvirtError

from src import sharedmod
from utils import xmlbuilder

required_params = ('poolname',)
optional_params = ()

def display_pool_info(stg, logger):
    """Display current storage pool information"""
    logger.debug("current defined storage pool: %s" % \
                  stg.defstorage_pool_list())
    logger.debug("current active storage pool: %s" % stg.storage_pool_list())

def activate_pool(params):
    """Undefine a storage pool that's been defined and inactive"""
    logger = params['logger']
    poolname = params['poolname']

    conn = sharedmod.libvirtobj['conn']
    pool_names = conn.listDefinedStoragePools()
    pool_names += conn.listStoragePools()

    if poolname in pool_names:
        poolobj = conn.storagePoolLookupByName(poolname)
    else:
        logger.error("%s not found\n" % poolname);
        return 1

    if poolobj.isActive():
        logger.error("%s is active already" % poolname)
        return 1

    try:
        poolobj.create(0)
        time.sleep(5)
        if  poolobj.isActive():
            logger.info("activating %s storage pool is SUCCESSFUL!!!" % poolname)
        else:
            logger.info("activating %s storage pool is UNSUCCESSFUL!!!" % poolname)
            return 1
    except libvirtError, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.message, e.get_error_code()))
        return 1

    return 0
