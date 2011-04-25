#!/usr/bin/env python
"""this test case is used for testing delete
   a logical type storage volume
"""

__author__ = 'Alex Jia: ajia@redhat.com'
__date__ = 'Thu April 22, 2010'
__version__ = '0.1.0'
__credits__ = 'Copyright (C) 2009 Red Hat, Inc.'
__all__ = ['usage', 'check_volume_delete', 'check_pool_inactive', \
           'get_storage_volume_number', 'display_volume_info', \
           'delete_logical_volume']

import os
import re
import sys
import commands

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
#    keys = ['poolname', 'volname', 'voltype', \
#'capacity', 'allocation', 'volpath']
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
    logger.info("current storage volume list: %s" \
% stg.get_volume_list(poolname))

def display_physical_volume():
    """Display current physical storage volume information"""
    stat, ret = commands.getstatusoutput("lvdisplay")
    logger.debug("lvdisplay command execute return value: %d" % stat)
    logger.debug("lvdisplay command execute return result: %s" % ret)

def get_storage_volume_number(stgobj, poolname):
    """Get storage volume number"""
    vol_num = stgobj.get_volume_number(poolname)
    logger.info("current storage volume number: %s" % vol_num)
    return vol_num

def check_pool_active(stgobj, poolname):
    """Check to make sure that the pool is active"""
    pool_names = stgobj.defstorage_pool_list()
    pool_names += stgobj.storage_pool_list()
    if poolname in pool_names:
        if stgobj.isActive_pool(poolname):
            return True
        else:
            logger.debug("%s pool is inactive" % poolname)
            return False
    else:
        logger.error("%s pool don't exist" % poolname)
        return False

def check_volume_delete(poolname, volkey):
    """Check storage volume result, poolname will exist under
       /etc/lvm/backup/ and lvdelete command is called if
       volume creation is successful
    """
    path = "/etc/lvm/backup/%s" % poolname
    logger.debug("%s file path: %s" % (poolname, path))
    if os.access(path, os.R_OK):
        logger.debug("execute grep lvremove %s command" % path)
        cmd="grep 'lvremove' %s" % (path)
        logger.debug(cmd)
        stat, ret = commands.getstatusoutput(cmd)
        if stat == 0:
            logger.debug(ret)
            return True
        else:
            logger.debug(ret)
            return False
    else:
        logger.debug("%s file don't exist" % path)
        return False

def delete_logical_volume(params):
    """Create a logical type storage volume"""
    global logger
    logger = params['logger']

    if not usage(params):
        return 1

    poolname = params['poolname']
    volname = params['volname']

    util = utils.Utils()
    uri = util.get_uri('127.0.0.1')

    conn = connectAPI.ConnectAPI()
    virconn = conn.open(uri)

    caps = conn.get_caps()
    logger.debug(caps)

    stgobj = storageAPI.StorageAPI(virconn)
    if not check_pool_active(stgobj, poolname):
        conn.close()
        logger.info("closed hypervisor connection")
        return 1

    volkey = stgobj.get_volume_key(poolname, volname)
    logger.debug("volume key: %s" % volkey)

    vol_num1 = get_storage_volume_number(stgobj, poolname)
    display_volume_info(stgobj, poolname)
    display_physical_volume()
    try:
        logger.info("delete %s storage volume" % volname)
        stgobj.delete_volume(poolname, volname)
        vol_num2 = get_storage_volume_number(stgobj, poolname)
        display_volume_info(stgobj, poolname)
        display_physical_volume()

        if vol_num1 > vol_num2 and check_volume_delete(poolname, volkey):
            logger.info("delete %s storage volume is successful" % volname)
            return 0
        else:
            logger.error("fail to delete %s storage volume" % volname)
            return 1
    except LibvirtAPI, e:
        logger.error("API error message: %s, error code is %s" \
                     % (e.response()['message'], e.response()['code']))
        return 1
    finally:
        conn.close()
        logger.info("closed hypervisor connection")

    return 0
