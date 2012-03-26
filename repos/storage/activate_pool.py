#!/usr/bin/env python
"""Test to activate an inactivate storage pool in libvirtd """

__author__ = 'Gurhan Ozen gozen@redhat.com'
__date__ = 'May 11, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2010 Red Hat, Inc.'
__all__ = ['usage', 'check_pool_activate', 'check_pool_inactive', \
           'display_pool_info', 'activate_pool']

import os
import re
import sys
import time

def append_path(path):
    """Append root path of package"""
    if path in sys.path:
        pass
    else:
        sys.path.append(path)

pwd = os.getcwd()
result = re.search('(.*)libvirt-test-API', pwd)
append_path(result.group(0))

from lib import connectAPI
from lib import storageAPI
from utils.Python import utils
from utils.Python import xmlbuilder
from exception import LibvirtAPI


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

def check_pool_active(stgobj, poolname, logger):
    """Check to make sure that the pool is defined and active"""
    pool_names = stgobj.defstorage_pool_list()
    pool_names += stgobj.storage_pool_list()
    if poolname in pool_names:
        if stgobj.isActive_pool(poolname):
            return True
        else:
            return False
    else:
        return False

def check_pool_inactive(stgobj, poolname, logger):
    """Check to make sure that the pool is defined and inactivate"""
    pool_names = stgobj.defstorage_pool_list()
    pool_names += stgobj.storage_pool_list()
    if poolname in pool_names:
        if stgobj.isActive_pool(poolname):
            return False
        else:
            return True
    else:
        return False

def activate_pool(params):
    """Undefine a storage pool that's been defined and inactive"""
    logger = params['logger']
    if usage(params):
        logger.info("Params are right")
    else:
        logger.info("Params are wrong")
        return 1

    poolname = params['poolname']

    util = utils.Utils()
    uri = params['uri']

    conn = connectAPI.ConnectAPI(uri)
    conn.open()

    stgobj = storageAPI.StorageAPI(conn)

    if not check_pool_inactive(stgobj, poolname, logger):
        logger.error("%s storage pool isn't defined or inactive" % poolname)
        conn.close()
        logger.info("closed hypervisor connection")
        return 1
    try:
        try:
            stgobj.active_pool(poolname)
            time.sleep(5)
            if check_pool_active(stgobj, poolname, logger):
                logger.info("activating %s storage pool is SUCCESSFUL!!!" % poolname)
                return 0
            else:
                logger.info("activating %s storage pool is UNSUCCESSFUL!!!" % poolname)
                return 1
        except LibvirtAPI, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.response()['message'], e.response()['code']))
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0
