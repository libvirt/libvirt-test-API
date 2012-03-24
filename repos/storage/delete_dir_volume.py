#!/usr/bin/env python
"""this test case is used for testing delete
   a volume from dir type storage pool
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Tue May 18, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2010 Red Hat, Inc.'
__all__ = ['usage', 'check_volume_delete', 'check_pool_inactive', \
           'get_storage_volume_number', 'display_volume_info', \
           'delete_dir_volume']

import os
import re
import sys

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
from exception import LibvirtAPI


def usage(params):
    """Verify inputing parameter dictionary"""
    keys = ['poolname', 'volname']
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

def display_volume_info(stg, poolname):
    """Display current storage volume information"""
    logger.debug("current storage volume list: %s" \
% stg.get_volume_list(poolname))

def get_storage_volume_number(stgobj, poolname):
    """Get storage volume number"""
    vol_num = stgobj.get_volume_number(poolname)
    logger.info("current storage volume number: %s" % vol_num)
    return vol_num

def check_pool_active(stgobj, poolname):
    """Check to make sure that the pool is active"""
    pool_names = stgobj.defstorage_pool_list()
    pool_names = stgobj.storage_pool_list()
    if poolname in pool_names:
        if stgobj.isActive_pool(poolname):
            return True
        else:
            logger.error("%s pool is inactive" % poolname)
            return False
    else:
        logger.error("%s pool don't exist" % poolname)
        return False

def check_volume_delete(volkey):
    """Check storage volume result, volname {volkey} will don't exist
       if deleting volume is successful
    """
    logger.debug("volume file path: %s" % volkey)
    if not os.access(volkey, os.R_OK):
        return True
    else:
        logger.debug("%s file don't exist" % volkey)
        return False

def delete_dir_volume(params):
    """Delete a dir type storage volume"""
    global logger
    logger = params['logger']

    if not usage(params):
        return 1

    poolname = params['poolname']
    volname = params['volname']

    util = utils.Utils()
    uri = params['uri']

    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    caps = conn.get_caps()
    logger.debug(caps)

    stgobj = storageAPI.StorageAPI(virconn)

    if not check_pool_active(stgobj, poolname):
        logger.error("can't delete volume from inactive %s pool" % poolname)
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    volkey = stgobj.get_volume_key(poolname, volname)
    logger.debug("volume key: %s" % volkey)

    vol_num1 = get_storage_volume_number(stgobj, poolname)
    display_volume_info(stgobj, poolname)

    try:
        try:
            logger.info("delete %s storage volume" % volname)
            stgobj.delete_volume(poolname, volname)
            vol_num2 = get_storage_volume_number(stgobj, poolname)
            display_volume_info(stgobj, poolname)
            if check_volume_delete(volkey) and vol_num1 > vol_num2:
                logger.info("delete %s storage volume is successful" % volname)
                return 0
            else:
                logger.error("%s storage volume is undeleted" % volname)
                return 1
        except LibvirtAPI, e:
            logger.error("API error message: %s, error code is %s" \
                         % (e.response()['message'], e.response()['code']))
            return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0
